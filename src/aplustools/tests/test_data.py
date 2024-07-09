from ..data import database, imagetools, updaters, faker_pro, advanced_imagetools, compressor
from ..data.noise import Noisy
import os


class TestUpdaters:
    def test_get_last_version(self):
        updater = updaters.GithubUpdater("adalfarus", "unicode-writer")
        versions = (updater.get_latest_tag_version(), updater.get_latest_release_title_version())
        assert versions in ((None, None), ("0.0.2", "0.0.2"))
        
    def test_local(self):
        assert updaters.local_test()


class TestDatabase:
    def test_local(self):
        assert database.local_test()


class TestFaker:
    def test_local(self):
        assert faker_pro.local_test()


class TestImagetools:
    def test_local(self):
        assert imagetools.local_test()


class TestAdvancedImagetools:
    def test_local(self):
        assert advanced_imagetools.local_test()


class TestCompressor:
    def test_local(self):
        assert compressor.local_test()


class TestNoise:
    def test_noise(self):
        try:
            # Generate and save noises for testing
            os.makedirs("./test_data/noises", exist_ok=True)
            os.chdir("./test_data/noises")

            noisy = Noisy()

            noises = {
                "white_noise.wav": noisy.generate_white_noise(5),
                "brown_noise.wav": noisy.generate_brown_noise(5),
                "pink_noise.wav": noisy.generate_pink_noise(5),
                "blue_noise.wav": noisy.generate_blue_noise(5),
                "violet_noise.wav": noisy.generate_violet_noise(5),
                "green_noise.wav": noisy.generate_green_noise(5),
                "balanced_noise.wav": noisy.generate_balanced_noise(5),
                "bright_noise.wav": noisy.generate_bright_noise(5),
                "gray_noise.wav": noisy.generate_gray_noise(5),
                "orange_noise.wav": noisy.generate_orange_noise(5),
                "dark_noise.wav": noisy.generate_dark_noise(5),
                "ocean_noise.wav": noisy.generate_ocean_noise(500),
                "rough_ocean_noise.wav": noisy.generate_rough_ocean_noise(5),
                "rain_noise.wav": noisy.generate_rain_noise(155, intensity=6),
                "stream_noise.wav": noisy.generate_stream_noise(5),
                "velvet_noise.wav": noisy.generate_velvet_noise(5),
                "black_noise.wav": noisy.generate_black_noise(5),
                "noisy_white_noise.wav": noisy.generate_noisy_white_noise(5),
                "noisy_black_noise.wav": noisy.generate_noisy_black_noise(5),
                "red_noise.wav": noisy.generate_red_noise(5)
            }

            # Save noises
            for filename, noise in noises.items():
                print(filename)
                noisy.visualize_noise_as_image(noise, f"{filename}.png")
                # noisy.visualize_noise_as_spectrogram_image(noise, f"{filename}.png")
                noisy.save_noise(f"./{filename}", noise)
        except Exception:
            assert False
        assert True
