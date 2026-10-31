import SwiftUI

final class ThemeManager: ObservableObject {
    static let shared = ThemeManager()
    
    @Published var isDarkMode = false
    
    private init() {}
    
    var primaryBackground: Color {
        Color(light: Color(hex: "FDF8F3"), dark: Color(hex: "2C1810"))
    }
    
    var secondaryBackground: Color {
        Color(light: Color(hex: "FFF9F0"), dark: Color(hex: "3A2218"))
    }
    
    var tertiaryBackground: Color {
        Color(light: Color(hex: "F5E6D3"), dark: Color(hex: "4A2E20"))
    }
    
    var cardBackground: Color {
        Color(light: Color(hex: "FFFFFF").opacity(0.85), dark: Color(hex: "2C1810").opacity(0.85))
    }
    
    var primaryText: Color {
        Color(light: Color(hex: "3C2415"), dark: Color(hex: "F5E6D3"))
    }
    
    var secondaryText: Color {
        Color(light: Color(hex: "8B4513"), dark: Color(hex: "CD853F"))
    }
    
    var tertiaryText: Color {
        Color(light: Color(hex: "A0522D"), dark: Color(hex: "DEB887"))
    }
    
    var accent: Color {
        Color(light: Color(hex: "D2691E"), dark: Color(hex: "FF8C00"))
    }
    
    var accentSubtle: Color {
        Color(light: Color(hex: "D2691E").opacity(0.12), dark: Color(hex: "FF8C00").opacity(0.18))
    }
    
    var success: Color {
        Color(light: Color(hex: "2E7D32"), dark: Color(hex: "66BB6A"))
    }
    
    var error: Color {
        Color(light: Color(hex: "C62828"), dark: Color(hex: "EF5350"))
    }
    
    var warning: Color {
        Color(light: Color(hex: "F57C00"), dark: Color(hex: "FFA726"))
    }
    
    var info: Color {
        Color(light: Color(hex: "1976D2"), dark: Color(hex: "42A5F5"))
    }
    
    var border: Color {
        Color(light: Color(hex: "8B4513").opacity(0.15), dark: Color(hex: "CD853F").opacity(0.25))
    }
    
    var cardBorder: Color {
        Color(light: Color(hex: "8B4513").opacity(0.15), dark: Color(hex: "CD853F").opacity(0.25))
    }
    
    var divider: Color {
        Color(light: Color(hex: "8B4513").opacity(0.1), dark: Color(hex: "CD853F").opacity(0.15))
    }
    
    var shadowColor: Color {
        Color(light: Color(hex: "8B4513").opacity(0.12), dark: Color.black.opacity(0.35))
    }
    
    var navBarBackground: Color { cardBackground }
    var navBarTitle: Color { primaryText }
    var navBarTint: Color { accent }
    var tabBarBackground: Color { cardBackground }
    var tabBarSelected: Color { accent }
    var tabBarUnselected: Color { tertiaryText }
    
    let radiusSmall: CGFloat = 8
    let radiusMedium: CGFloat = 12
    let radiusLarge: CGFloat = 16
    let radiusXL: CGFloat = 20
    let radiusFull: CGFloat = 100
    
    let spacingXS: CGFloat = 4
    let spacingS: CGFloat = 8
    let spacingM: CGFloat = 12
    let spacingL: CGFloat = 16
    let spacingXL: CGFloat = 20
    let spacingXXL: CGFloat = 24
    let spacingSection: CGFloat = 32
    
    let shadowRadiusSmall: CGFloat = 8
    let shadowRadiusMedium: CGFloat = 16
    let shadowRadiusLarge: CGFloat = 24
    
    var springSnappy: Animation {
        .spring(response: 0.3, dampingFraction: 0.7)
    }
    
    var springSmooth: Animation {
        .spring(response: 0.5, dampingFraction: 0.8)
    }
    
    var springBouncy: Animation {
        .spring(response: 0.4, dampingFraction: 0.6)
    }
    
    var easeQuick: Animation {
        .easeOut(duration: 0.2)
    }
    
    var easeMedium: Animation {
        .easeInOut(duration: 0.3)
    }
}

extension Color {
    init(light: Color, dark: Color) {
        self.init(uiColor: UIColor { traits in
            traits.userInterfaceStyle == .dark ? UIColor(dark) : UIColor(light)
        })
    }
    
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r, g, b, a: UInt64
        switch hex.count {
        case 6: (r, g, b, a) = ((int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF, 255)
        case 8: (r, g, b, a) = ((int >> 24) & 0xFF, (int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF)
        default: (r, g, b, a) = (0, 0, 0, 255)
        }
        self.init(.sRGB, red: Double(r)/255, green: Double(g)/255, blue: Double(b)/255, opacity: Double(a)/255)
    }
}