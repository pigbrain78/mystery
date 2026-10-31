import SwiftUI

@main
struct ManusOmniApp: App {
    @StateObject private var themeManager = ThemeManager.shared
    @StateObject private var appState = AppState()
    @StateObject private var eventManager = SimpleForegroundLogger.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .preferredColorScheme(themeManager.isDarkMode ? .dark : .light)
        }
    }
}

class AppState: ObservableObject {
    @Published var isInitialized = false
    @Published var currentScreen: AppScreen = .splash
    
    enum AppScreen {
        case splash
        case dashboard
    }
}