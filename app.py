from flask import Flask, render_template, jsonify, request, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Product, Track
import os
from werkzeug.utils import secure_filename
import stripe
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-for-development')
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# Make sure instance path exists
os.makedirs(app.instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'delus.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/music'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Create tables
with app.app_context():
    db.create_all()

def create_sample_data():
    # Check if we already have products
    if Product.query.first() is None:
        # Add sample products
        products = [
            Product(
                name="Ritual Trucker - Black XL",
                description="Essential Delus trucker",
                price=60.00,
                image_url="images/collection/item1.jpg",
                category="Clothing",
                stock=20
            ),
            Product(
                name="Ritual Trucker - Grey XL",
                description="Second Edition Delus trucker",
                price=60.00,
                image_url="images/collection/item2.jpg",
                category="Clothing",
                stock=20
            ),
            Product(
                name="Ritual Trucker - Maroon",
                description="Maroon Edition Delus trucker",
                price=60.00,
                image_url="images/collection/item3.jpg",
                category="Clothing",
                stock=20
            ),
            Product(
                name="Certified Trucker - Rose",
                description="Rose Edition Delus trucker",
                price=60.00,
                image_url="images/collection/item4.jpg",
                category="Clothing",
                stock=20
            ),
            Product(
                name="Certified Trucker - White",
                description="White Edition Delus trucker",
                price=60.00,
                image_url="images/collection/item5.jpg",
                category="Clothing",
                stock=20
            ),
            Product(
                name="Certified Trucker - Black",
                description="Black Edition Delus trucker",
                price=60.00,
                image_url="images/collection/item6.jpg",
                category="Clothing",
                stock=20
            )
        ]
        for product in products:
            db.session.add(product)
        
        # Add sample tracks
        tracks = [
            Track(
                title="Games (Remastered)",
                artist="German Brigante",
                cover_url="featured-track.jpg",
                audio_url="https://soundcloud.com/german-brigante/german-brigante-games-pura",
                source_type="soundcloud",
                featured=True
            ),
            Track(
                title="Kettenkarussell - Maybe",
                artist="Da Brøski",
                cover_url="featured-track.jpg",
                audio_url="https://api.soundcloud.com/tracks/470610045",
                source_type="soundcloud",
                featured=False
            ),
            Track(
                title="Delus Feature: Traxler",
                artist="Traxler",
                cover_url="featured-track.jpg",
                audio_url="https://api.soundcloud.com/tracks/1825112544",
                source_type="soundcloud",
                featured=False
            )
        ]
        for track in tracks:
            db.session.add(track)
        
        # Add sample releases
        releases = [
            Track(
                title="Delus Feature: Traxler",
                artist="Traxler",
                cover_url="featured-track.jpg",
                audio_url="https://api.soundcloud.com/tracks/1825112544",
                source_type="soundcloud",
                featured=False,
                is_release=True  # Only one release is marked
            )
        ]
        for release in releases:
            db.session.add(release)
        
        db.session.commit()

def reset_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        # Add sample data
        create_sample_data()

# Call create_sample_data after db.create_all()
with app.app_context():
    db.create_all()
    create_sample_data()

# Initialize session-based cart
@app.before_request
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []

@app.route('/')
def home():
    featured_products = Product.query.limit(4).all()
    featured_track = Track.query.filter_by(featured=True).first()
    releases = Track.query.filter_by(is_release=True).all()
    return render_template('index.html', 
                         products=featured_products, 
                         featured_track=featured_track,
                         releases=releases)

@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'image': p.image_url
    } for p in products])

@app.route('/api/playlist')
def get_playlist():
    tracks = Track.query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'artist': t.artist,
        'cover': t.cover_url,
        'url': t.audio_url
    } for t in tracks])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-track', methods=['POST'])
def upload_track():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_track = Track(
            title=request.form.get('title', 'Untitled'),
            artist=request.form.get('artist', 'Unknown'),
            cover_url=request.form.get('cover_url', 'default-cover.jpg'),
            source_type='local',
            source_url=f'music/{filename}'
        )
        db.session.add(new_track)
        db.session.commit()
        
        return jsonify({'message': 'Track uploaded successfully'})
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    # Check stock availability
    if product.stock < quantity:
        return jsonify({
            'error': 'Not enough stock available',
            'available_stock': product.stock
        }), 400
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Map product ID to correct image URL (the first image from carousel)
    product_images = {
        1: 'images/hats/DSC09089.jpg',
        2: 'images/hats/DSC09203.JPG',
        3: 'images/hats/DSC09114.JPG',
        4: 'images/hats/DSC09155.JPG',
        5: 'images/hats/DSC09180.JPG',
        6: 'images/hats/DSC09135.jpg'
    }
    
    # Check if product already in cart
    cart = session['cart']
    item_found = False
    current_cart_quantity = 0
    
    for item in cart:
        if item['id'] == product_id:
            current_cart_quantity = item['quantity']
            # Check if adding more would exceed stock
            if current_cart_quantity + quantity > product.stock:
                return jsonify({
                    'error': f'Only {product.stock - current_cart_quantity} more items available',
                    'available_stock': product.stock - current_cart_quantity
                }), 400
            item['quantity'] += quantity
            item_found = True
            break
    
    if not item_found:
        cart.append({
            'id': product_id,
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'image_url': product_images.get(product_id, product.image_url)
        })
    
    session['cart'] = cart
    return jsonify({
        'success': True,
        'message': 'Product added to cart',
        'cart_total': len(cart),
        'product': {
            'name': product.name,
            'price': float(product.price),
            'image_url': product_images.get(product_id, product.image_url)
        }
    })

@app.route('/cart')
def cart():
    cart_products = []
    if 'cart' in session and session['cart']:
        cart_products = Product.query.filter(Product.id.in_(session['cart'])).all()
    return render_template('cart.html', products=cart_products)

@app.route('/shipping')
def shipping():
    return render_template('shipping.html')

@app.route('/returns')
def returns():
    return render_template('returns.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt', mimetype='text/plain')

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        session['cart'] = [item for item in cart if item['id'] != product_id]
    return redirect(url_for('cart'))

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        cart = session.get('cart', [])
        
        if not cart:
            return jsonify({'error': 'Your cart is empty'}), 400
        
        line_items = [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item['name'],
                    'images': [request.host_url + 'static/' + item['image_url']] if item.get('image_url') else [],
                },
                'unit_amount': int(item['price'] * 100),  # Stripe expects amounts in cents
            },
            'quantity': item['quantity'],
        } for item in cart]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'cart',
            shipping_address_collection={
                'allowed_countries': ['US', 'CA'],  # Add countries you ship to
            },
            shipping_options=[
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'fixed_amount': {'amount': 0, 'currency': 'usd'},
                        'display_name': 'Free shipping',
                        'delivery_estimate': {
                            'minimum': {'unit': 'business_day', 'value': 5},
                            'maximum': {'unit': 'business_day', 'value': 7},
                        }
                    }
                }
            ]
        )
        
        # Clear the cart after successful checkout session creation
        if checkout_session.id:
            session['cart'] = []
            
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    if session_id:
        try:
            # Retrieve the checkout session to verify payment
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            # You could save order details to your database here
            # customer_email = checkout_session.customer_details.email
            # shipping_details = checkout_session.shipping
            
            return render_template('success.html', 
                                  session_id=session_id,
                                  customer_email=checkout_session.customer_details.email if hasattr(checkout_session, 'customer_details') else None)
        except Exception as e:
            # Handle any errors
            return render_template('success.html', error=str(e))
    
    return render_template('success.html')

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({'error': str(e)}), 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        checkout_session = event['data']['object']
        
        # Process the order and reduce inventory
        try:
            # Get line items from the checkout session
            line_items = stripe.checkout.Session.list_line_items(checkout_session.id)
            
            for item in line_items['data']:
                # You'll need to match Stripe line items to your products
                # This is a simplified version - you might want to store product IDs in metadata
                product_name = item['description']
                quantity_purchased = item['quantity']
                
                # Find product by name (you might want to use a better matching method)
                product = Product.query.filter_by(name=product_name).first()
                if product:
                    # Reduce stock
                    product.stock = max(0, product.stock - quantity_purchased)
                    db.session.commit()
                    print(f"Reduced stock for {product.name}: {quantity_purchased} items. New stock: {product.stock}")
            
            print(f"Order completed for session: {checkout_session.id}")
            
        except Exception as e:
            print(f"Error processing inventory: {str(e)}")
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)

# reset_db()
