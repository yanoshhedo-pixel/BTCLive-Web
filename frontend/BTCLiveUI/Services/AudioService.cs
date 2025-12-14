using System.IO;
using System.Media;
using System.Windows;

namespace BTCLiveUI.Services
{
    /// <summary>
    /// Audio service for playing alert sounds
    /// </summary>
    public class AudioService
    {
        private readonly SoundPlayer _soundPlayer;
        private bool _soundEnabled = true;

        public bool SoundEnabled
        {
            get => _soundEnabled;
            set => _soundEnabled = value;
        }

        public AudioService()
        {
            _soundPlayer = new SoundPlayer();
        }

        public void PlayAlertSound()
        {
            if (!_soundEnabled)
                return;

            try
            {
                // Try to load custom alert sound
                var alertSoundPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Assets", "alert.wav");
                
                if (File.Exists(alertSoundPath))
                {
                    _soundPlayer.SoundLocation = alertSoundPath;
                    _soundPlayer.Play();
                }
                else
                {
                    // Fallback to system beep
                    System.Console.Beep(800, 200);
                }
            }
            catch (Exception ex)
            {
                // Fallback to system beep on error
                try
                {
                    System.Console.Beep(800, 200);
                }
                catch
                {
                    // Silent failure if beep also fails
                }
            }
        }

        public void PlayNotificationSound()
        {
            if (!_soundEnabled)
                return;

            try
            {
                System.Console.Beep(600, 100);
            }
            catch
            {
                // Silent failure
            }
        }
    }
}
