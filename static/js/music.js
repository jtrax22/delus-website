document.addEventListener('DOMContentLoaded', function() {
    // Track player elements
    const playButtons = document.querySelectorAll('.play-button');
    const progressBar = document.querySelector('.progress');
    const timeDisplay = document.querySelector('.time');
    let isPlaying = false;
    let currentTrack = null;

    // Handle play button clicks
    playButtons.forEach(button => {
        button.addEventListener('click', function() {
            const trackCard = this.closest('.track-card') || this.closest('.track-player');
            
            if (currentTrack && currentTrack !== trackCard) {
                // Stop previous track
                resetTrackUI(currentTrack);
            }

            if (this.classList.contains('playing')) {
                pauseTrack(trackCard);
            } else {
                playTrack(trackCard);
            }
        });
    });

    function playTrack(trackCard) {
        const playButton = trackCard.querySelector('.play-button i');
        playButton.classList.remove('fa-play');
        playButton.classList.add('fa-pause');
        trackCard.querySelector('.play-button').classList.add('playing');
        currentTrack = trackCard;
        isPlaying = true;
        
        // Simulate progress updates
        startProgressSimulation();
    }

    function pauseTrack(trackCard) {
        resetTrackUI(trackCard);
        isPlaying = false;
    }

    function resetTrackUI(trackCard) {
        const playButton = trackCard.querySelector('.play-button i');
        playButton.classList.remove('fa-pause');
        playButton.classList.add('fa-play');
        trackCard.querySelector('.play-button').classList.remove('playing');
    }

    function startProgressSimulation() {
        // This is a placeholder for actual audio progress
        // In a real implementation, this would sync with actual audio playback
        let progress = 0;
        const interval = setInterval(() => {
            if (!isPlaying) {
                clearInterval(interval);
                return;
            }
            progress += 1;
            if (progress > 100) {
                progress = 0;
                pauseTrack(currentTrack);
            }
            updateProgress(progress);
        }, 1000);
    }

    function updateProgress(value) {
        progressBar.style.width = `${value}%`;
        const minutes = Math.floor(value * 3.45 / 100);
        const seconds = Math.floor((value * 3.45 / 100 - minutes) * 60);
        timeDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')} / 3:45`;
    }
}); 