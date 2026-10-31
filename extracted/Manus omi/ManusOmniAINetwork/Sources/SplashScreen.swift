import SwiftUI

struct SplashScreen: View {
    @ObservedObject var theme = ThemeManager.shared
    @EnvironmentObject var appState: AppState
    @State private var isAnimating = false
    @State private var statusMessage = "Initializing Node..."
    
    var body: some View {
        ZStack {
            theme.primaryBackground
                .ignoresSafeArea()
            
            VStack(spacing: theme.spacingXXL) {
                Spacer()
                
                Image(systemName: "cube.fill")
                    .font(.system(size: 80, weight: .bold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [theme.accent, theme.secondaryText],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .scaleEffect(isAnimating ? 1.1 : 1.0)
                    .animation(theme.springBouncy.repeatForever(autoreverses: true), value: isAnimating)
                
                Text("Manus Omni")
                    .font(.system(size: 34, weight: .bold, design: .rounded))
                    .foregroundColor(theme.primaryText)
                
                VStack(spacing: theme.spacingM) {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: theme.accent))
                        .scaleEffect(1.2)
                    
                    Text(statusMessage)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(theme.secondaryText)
                }
                .padding(.top, theme.spacingXL)
                
                Spacer()
                
                Text("AI Network")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(theme.tertiaryText)
                    .padding(.bottom, theme.spacingXL)
            }
            .padding(.horizontal, theme.spacingXL)
        }
        .onAppear {
            isAnimating = true
            initializeNode()
        }
    }
    
    private func initializeNode() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            statusMessage = "Node Identity Verified"
        }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            withAnimation(theme.springSmooth) {
                appState.currentScreen = .dashboard
                appState.isInitialized = true
            }
        }
    }
}