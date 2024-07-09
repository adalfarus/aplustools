import numpy as np
from scipy.io.wavfile import write
from PIL import Image
from scipy.signal import butter, filtfilt


class Noisy:
    """A simple class to generate different noises."""
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def noise_psd(self, N, psd=lambda f: 1):
        """Generate noise with a given power spectral density."""
        X_white = np.fft.rfft(np.random.randn(N))
        S = psd(np.fft.rfftfreq(N))
        # Normalize S
        S = S / np.sqrt(np.mean(S ** 2))
        X_shaped = X_white * S
        return np.fft.irfft(X_shaped)

    def generate_white_noise(self, duration: int, intensity: float = 1.0):
        """Generate white noise, spread across all spectrums."""
        return self.noise_psd(int(self.sample_rate * duration), lambda f: 1) * intensity

    def generate_brown_noise(self, duration: int, intensity: float = 1.0):
        """Generate brown noise, emphasizing deeper tones."""
        num_samples = int(duration * self.sample_rate)
        brown_noise = np.cumsum(np.random.randn(num_samples))
        brown_noise *= intensity / np.max(np.abs(brown_noise))
        return brown_noise

    def generate_pink_noise(self, duration: int, intensity: float = 1.0):
        """Generate pink noise, which has equal energy per octave."""
        return self.noise_psd(int(self.sample_rate * duration), lambda f: 1 / np.where(f == 0, float('inf'), np.sqrt(f))) * intensity

    def generate_blue_noise(self, duration: int, intensity: float = 1.0):
        """Generate blue noise, which emphasizes higher frequencies."""
        return self.noise_psd(int(self.sample_rate * duration), lambda f: np.sqrt(f)) * intensity

    def generate_violet_noise(self, duration: int, intensity: float = 1.0):
        """Generate violet noise, which emphasizes even higher frequencies."""
        return self.noise_psd(int(self.sample_rate * duration), lambda f: f) * intensity

    def generate_green_noise(self, duration: int, intensity: float = 1.0):
        """Generate green noise, similar to pink noise but with emphasis around 500 Hz."""
        return self.noise_psd(int(self.sample_rate * duration), lambda f: 1 / np.where(f == 0, float('inf'), f**0.5 * (1 - f)**0.5)) * intensity

    def generate_balanced_noise(self, duration: int, intensity: float = 1.0):
        """Generate balanced noise, a mix of white, pink, and brown noise."""
        return self.noise_psd(int(self.sample_rate * duration), lambda f: 1 / np.where(f == 0, float('inf'), (1 + f**2)**0.5)) * intensity

    def generate_bright_noise(self, duration: int, intensity: float = 1.0):
        """Generate bright noise, which emphasizes higher frequencies."""
        return self.noise_psd(int(self.sample_rate * duration), lambda f: f**2) * intensity

    def generate_gray_noise(self, duration: int, intensity: float = 1.0):
        """Generate gray noise, perceptually uniform noise."""
        num_samples = int(self.sample_rate * duration)
        white_noise = np.random.normal(0, 1, num_samples)
        gray_noise = np.fft.rfft(white_noise)
        freqs = np.fft.rfftfreq(num_samples, 1 / self.sample_rate)
        contour = np.sqrt(1 / (1 + (freqs / 1000) ** 2))
        gray_noise *= contour
        gray_noise = np.fft.irfft(gray_noise, n=num_samples)
        # Apply a larger moving average to smooth the noise
        gray_noise = np.convolve(gray_noise, np.ones(10000) / 10000, mode='same')
        gray_noise *= intensity / np.max(np.abs(gray_noise))
        return gray_noise

    def generate_orange_noise(self, duration, intensity=1.0):
        """Generate orange noise, low-pass filtered white noise."""
        white_noise = self.generate_white_noise(duration)
        orange_noise = np.fft.rfft(white_noise)
        freqs = np.fft.rfftfreq(len(white_noise), 1 / self.sample_rate)
        orange_noise *= (freqs < 1000)
        orange_noise = np.fft.irfft(orange_noise)
        orange_noise *= intensity / np.max(np.abs(orange_noise))
        return orange_noise

    def generate_dark_noise(self, duration, intensity=1.0):
        """Generate dark noise, emphasizing lower frequencies."""
        white_noise = self.generate_white_noise(duration)
        dark_noise = np.fft.rfft(white_noise)
        freqs = np.fft.rfftfreq(len(white_noise), 1 / self.sample_rate)
        dark_noise *= (freqs < 500)
        dark_noise = np.fft.irfft(dark_noise)
        dark_noise *= intensity / np.max(np.abs(dark_noise))
        return dark_noise

    def generate_rain_noise(self, duration, intensity=0.5):
        """Generate rain noise, mimicking the sound of rain."""
        fs = self.sample_rate  # Sample rate
        t = np.linspace(0, duration, int(fs * duration), endpoint=False)

        # Generate gray noise
        rain_noise = self.generate_gray_noise(duration, intensity)

        # Apply a convolution to create a base rain sound
        rain_noise = np.convolve(rain_noise, np.ones(100) / 100, mode='same')

        # Modulate the amplitude of the gray noise with a sinusoidal function
        modulation_frequency = 0.1  # Frequency of the modulation in Hz
        modulation = 1 + 0.5 * np.sin(2 * np.pi * modulation_frequency * t)
        rain_noise *= modulation  # Apply the modulation to the rain noise

        # Generate and add raindrops
        raindrop_intensity = intensity * 0.5  # Reduce the intensity of raindrops
        raindrop_probability = 0.1 * intensity  # Scale probability with intensity
        raindrop_distribution = np.random.choice([0, 1 * raindrop_intensity], size=rain_noise.shape,
                                                 p=[1 - raindrop_probability, raindrop_probability])
        raindrop_distribution = raindrop_distribution * np.random.normal(1, 0.2, size=rain_noise.shape)

        rain_noise += raindrop_distribution

        # Normalize the rain noise
        rain_noise *= intensity / np.max(np.abs(rain_noise))

        # Apply a gentle low-pass filter to smooth out the noise without removing too much
        def low_pass_filter(data, cutoff=5000, fs=44100, order=3):
            nyquist = 0.5 * fs
            normal_cutoff = cutoff / nyquist
            b, a = butter(order, normal_cutoff, btype='low', analog=False)
            y = filtfilt(b, a, data)
            return y

        rain_noise = low_pass_filter(rain_noise)

        return rain_noise

    def generate_ocean_noise(self, duration, intensity=1.0):
        """Generate ocean noise, mimicking the sound of ocean waves."""
        ocean_wave_freq = 0.1  # Frequency to simulate ocean waves
        time = np.arange(self.sample_rate * duration) / self.sample_rate

        # Base wave
        ocean_noise = np.sin(2 * np.pi * ocean_wave_freq * time) * (4 * intensity)

        # Adding layers of noise
        ocean_noise += self.generate_brown_noise(duration, intensity=intensity * 0.5)
        ocean_noise += self.generate_white_noise(duration, intensity=intensity * 0.3)

        # Smooth the combined noise
        ocean_noise = np.convolve(ocean_noise, np.ones(1000) / 1000, mode='same')

        # Normalize and amplify
        ocean_noise *= np.max(np.abs(ocean_noise))
        ocean_noise = ocean_noise[:int(self.sample_rate * duration)]  # Ensure correct length

        return ocean_noise

    def generate_rough_ocean_noise(self, duration, intensity=1.0):
        """Generate rough ocean noise, mimicking heavy ocean waves."""
        ocean_noise = self.generate_white_noise(duration)
        ocean_noise = np.convolve(ocean_noise, np.ones(100) / 100, mode='same')
        ocean_noise += self.generate_brown_noise(duration) * 0.1  # Reduced intensity
        # Add some variability to simulate a stream
        ocean_variability = self.generate_white_noise(duration, intensity=0.1)  # Reduced intensity
        ocean_variability = np.convolve(ocean_variability, np.ones(500) / 500, mode='same')
        ocean_noise += ocean_variability
        ocean_noise *= intensity / np.max(np.abs(ocean_noise))
        ocean_noise = ocean_noise[:int(self.sample_rate * duration)]  # Ensure correct length
        return ocean_noise

    def generate_stream_noise(self, duration, intensity=1.0):
        """Generate stream noise, mimicking the sound of a babbling brook."""
        stream_noise = self.generate_white_noise(duration, intensity=0.05)  # Low intensity white noise
        stream_noise = np.convolve(stream_noise, np.ones(50) / 50, mode='same')  # Smooth the noise
        stream_bubbles = self.generate_white_noise(duration, intensity=0.02)  # Low intensity for bubbling
        bubble_freqs = np.fft.rfftfreq(len(stream_bubbles), 1 / self.sample_rate)
        bubble_mask = (bubble_freqs > 100) & (bubble_freqs < 1000)  # Focus on mid frequencies for bubbles
        stream_bubbles_fft = np.fft.rfft(stream_bubbles)
        stream_bubbles_fft *= bubble_mask
        stream_bubbles = np.fft.irfft(stream_bubbles_fft, n=len(stream_bubbles))
        stream_bubbles = np.convolve(stream_bubbles, np.ones(200) / 200, mode='same')  # Smooth the bubbles

        stream_noise += stream_bubbles
        stream_noise *= intensity / np.max(np.abs(stream_noise))
        stream_noise = stream_noise[:int(self.sample_rate * duration)]  # Ensure correct length
        return stream_noise

    def generate_velvet_noise(self, duration: int, intensity: float = 1.0):
        """Generate velvet noise, sparse impulses with smooth interpolation."""
        num_samples = int(self.sample_rate * duration)
        density = 0.01  # Proportion of non-zero samples
        noise = np.zeros(num_samples)
        indices = np.random.choice(np.arange(num_samples), size=int(density * num_samples), replace=False)
        noise[indices] = np.random.randn(len(indices)) * intensity
        return np.convolve(noise, np.ones(50) / 50, mode='same')  # Smooth the impulses

    def generate_black_noise(self, duration: int, intensity: float = 1.0):
        """Generate black noise, very low amplitude noise."""
        num_samples = int(self.sample_rate * duration)
        noise = np.random.normal(0, intensity * 0.01, num_samples)  # Very low intensity
        return noise

    def generate_noisy_white_noise(self, duration: int, intensity: float = 1.0):
        """Generate noisy white noise, white noise with varying intensity."""
        white_noise = self.generate_white_noise(duration)
        modulator = np.random.randn(int(self.sample_rate * duration)) * intensity
        noisy_white_noise = white_noise * modulator
        return noisy_white_noise

    def generate_noisy_black_noise(self, duration: int, intensity: float = 1.0):
        """Generate noisy black noise, very low amplitude noise with variation."""
        black_noise = self.generate_black_noise(duration)
        modulator = np.random.randn(int(self.sample_rate * duration)) * intensity
        noisy_black_noise = black_noise * (1 + modulator * 0.1)  # Slight variation
        return noisy_black_noise

    def generate_red_noise(self, duration: int, intensity: float = 1.0):
        """Generate red noise, also known as brownian noise, emphasizing deeper tones."""
        num_samples = int(self.sample_rate * duration)
        red_noise = np.cumsum(np.random.randn(num_samples))
        red_noise *= intensity / np.max(np.abs(red_noise))
        return red_noise

    def save_noise(self, filename, noise):
        """Save the generated noise to a file."""
        write(filename, self.sample_rate, noise.astype(np.float32))

    def visualize_noise_as_image(self, noise, filename):
        """Convert noise to an image and save it."""
        noise_min, noise_max = noise.min(), noise.max()
        noise_normalized = (noise - noise_min) / (noise_max - noise_min) * 255
        noise_normalized = noise_normalized.astype(np.uint8)

        # Create an image from the normalized noise
        height = 256  # Height of the image
        width = len(noise_normalized) // height
        noise_image = noise_normalized[:height * width].reshape((height, width))

        image = Image.fromarray(noise_image, mode='L')
        image.save(filename)

    def visualize_noise_as_spectrogram_image(self, noise, filename):
        """Convert noise to an image and save it as a spectrogram."""
        from scipy.signal import spectrogram

        # Compute the spectrogram
        f, t, Sxx = spectrogram(noise, self.sample_rate)

        # Convert the power spectrogram (Sxx) to dB scale
        Sxx = 10 * np.log10(Sxx)
        Sxx = np.flipud(Sxx)  # Flip to match image orientation

        # Normalize to 0-255 range
        Sxx -= Sxx.min()
        Sxx /= Sxx.max()
        Sxx *= 255
        Sxx = Sxx.astype(np.uint8)

        # Convert to an image
        image = Image.fromarray(Sxx)
        image.save(filename)
