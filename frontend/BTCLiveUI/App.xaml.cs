using System.Windows;
using BTCLiveUI.Services;
using BTCLiveUI.ViewModels;

namespace BTCLiveUI
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // Initialize services
            var wsService = new WebSocketService();
            var audioService = new AudioService();

            // Create main window with view model
            var mainViewModel = new MainViewModel(wsService, audioService);
            var mainWindow = new MainWindow
            {
                DataContext = mainViewModel
            };

            mainWindow.Show();
        }
    }
}
