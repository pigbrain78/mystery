import SwiftUI

struct SettingsView: View {
    @ObservedObject var theme = ThemeManager.shared
    @StateObject private var viewModel = SettingsViewModel()
    @Environment(\.dismiss) var dismiss
    @State private var showResetConfirmation = false
    
    var body: some View {
        ZStack {
            theme.primaryBackground
                .ignoresSafeArea()
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: theme.spacingXXL) {
                    networkSettingsSection
                    
                    loggingSettingsSection
                    
                    appSettingsSection
                    
                    aboutSection
                    
                    actionButtons
                }
                .padding(.horizontal, theme.spacingL)
                .padding(.top, theme.spacingM)
                .padding(.bottom, 100)
            }
        }
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .cancellationAction) {
                Button("Done") {
                    dismiss()
                }
                .foregroundColor(theme.accent)
            }
        }
        .alert("Reset Settings", isPresented: $showResetConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("Reset", role: .destructive) {
                viewModel.resetToDefaults()
            }
        } message: {
            Text("Are you sure you want to reset all settings to their default values?")
        }
        .task {
            await viewModel.loadSettings()
        }
    }
    
    private var networkSettingsSection: some View {
        VStack(alignment: .leading, spacing: theme.spacingL) {
            sectionHeader(title: "Network Settings", icon: "network")
            
            VStack(spacing: theme.spacingL) {
                settingInputField(
                    label: "Port Number",
                    value: $viewModel.portNumber,
                    placeholder: "5005",
                    keyboardType: .numberPad
                )
                
                settingToggle(
                    label: "Auto-Discovery",
                    description: "Automatically discover peers on network startup",
                    isOn: $viewModel.autoDiscovery
                )
            }
            .padding(theme.spacingL)
            .background(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .fill(theme.cardBackground)
                    .shadow(color: theme.shadowColor, radius: theme.shadowRadiusSmall, x: 0, y: 4)
            )
            .overlay(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .stroke(theme.cardBorder, lineWidth: 1)
            )
        }
    }
    
    private var loggingSettingsSection: some View {
        VStack(alignment: .leading, spacing: theme.spacingL) {
            sectionHeader(title: "Logging Settings", icon: "doc.text")
            
            VStack(spacing: theme.spacingL) {
                settingToggle(
                    label: "Verbose Logging",
                    description: "Enable detailed logging of all handshake attempts and task syncs",
                    isOn: $viewModel.verboseLogging
                )
                
                settingDropdown(
                    label: "Log Retention",
                    description: "How long to keep sync logs",
                    selection: $viewModel.logRetention,
                    options: viewModel.logRetentionOptions
                )
            }
            .padding(theme.spacingL)
            .background(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .fill(theme.cardBackground)
                    .shadow(color: theme.shadowColor, radius: theme.shadowRadiusSmall, x: 0, y: 4)
            )
            .overlay(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .stroke(theme.cardBorder, lineWidth: 1)
            )
        }
    }
    
    private var appSettingsSection: some View {
        VStack(alignment: .leading, spacing: theme.spacingL) {
            sectionHeader(title: "App Settings", icon: "slider.horizontal.3")
            
            VStack(spacing: theme.spacingL) {
                settingInputField(
                    label: "Handshake Timeout",
                    value: $viewModel.handshakeTimeout,
                    placeholder: "3000",
                    keyboardType: .numberPad,
                    suffix: "ms"
                )
            }
            .padding(theme.spacingL)
            .background(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .fill(theme.cardBackground)
                    .shadow(color: theme.shadowColor, radius: theme.shadowRadiusSmall, x: 0, y: 4)
            )
            .overlay(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .stroke(theme.cardBorder, lineWidth: 1)
            )
        }
    }
    
    private var aboutSection: some View {
        VStack(alignment: .leading, spacing: theme.spacingL) {
            sectionHeader(title: "About", icon: "info.circle")
            
            VStack(spacing: theme.spacingM) {
                infoRow(label: "App Version", value: viewModel.appVersion)
                infoRow(label: "Build Number", value: viewModel.buildNumber)
                infoRow(label: "Device Node ID", value: viewModel.deviceNodeId)
            }
            .padding(theme.spacingL)
            .background(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .fill(theme.cardBackground)
                    .shadow(color: theme.shadowColor, radius: theme.shadowRadiusSmall, x: 0, y: 4)
            )
            .overlay(
                RoundedRectangle(cornerRadius: theme.radiusLarge)
                    .stroke(theme.cardBorder, lineWidth: 1)
            )
        }
    }
    
    private var actionButtons: some View {
        VStack(spacing: theme.spacingM) {
            Button {
                Task {
                    await viewModel.saveSettings()
                    dismiss()
                }
            } label: {
                HStack {
                    Image(systemName: "checkmark.circle")
                    Text("Save Settings")
                }
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, theme.spacingL)
                .background(
                    RoundedRectangle(cornerRadius: theme.radiusMedium)
                        .fill(theme.accent)
                )
            }
            
            Button {
                showResetConfirmation = true
            } label: {
                HStack {
                    Image(systemName: "arrow.counterclockwise")
                    Text("Reset to Defaults")
                }
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(theme.error)
                .frame(maxWidth: .infinity)
                .padding(.vertical, theme.spacingL)
                .background(
                    RoundedRectangle(cornerRadius: theme.radiusMedium)
                        .fill(theme.error.opacity(0.1))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: theme.radiusMedium)
                        .stroke(theme.error, lineWidth: 1)
                )
            }
        }
    }
    
    private func sectionHeader(title: String, icon: String) -> some View {
        HStack(spacing: theme.spacingM) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(theme.accent)
            
            Text(title)
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(theme.primaryText)
        }
    }
    
    private func settingInputField(label: String, value: Binding<String>, placeholder: String, keyboardType: UIKeyboardType = .default, suffix: String? = nil) -> some View {
        VStack(alignment: .leading, spacing: theme.spacingS) {
            Text(label)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(theme.secondaryText)
            
            HStack {
                TextField(placeholder, text: value)
                    .font(.system(size: 17))
                    .foregroundColor(theme.primaryText)
                    .keyboardType(keyboardType)
                
                if let suffix = suffix {
                    Text(suffix)
                        .font(.system(size: 14))
                        .foregroundColor(theme.tertiaryText)
                }
            }
            .padding(theme.spacingM)
            .background(theme.tertiaryBackground)
            .clipShape(RoundedRectangle(cornerRadius: theme.radiusSmall))
            .overlay(
                RoundedRectangle(cornerRadius: theme.radiusSmall)
                    .stroke(theme.border, lineWidth: 1)
            )
        }
    }
    
    private func settingToggle(label: String, description: String, isOn: Binding<Bool>) -> some View {
        VStack(alignment: .leading, spacing: theme.spacingS) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(label)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(theme.primaryText)
                    
                    Text(description)
                        .font(.system(size: 13))
                        .foregroundColor(theme.secondaryText)
                        .fixedSize(horizontal: false, vertical: true)
                }
                
                Spacer()
                
                Toggle("", isOn: isOn)
                    .labelsHidden()
                    .tint(theme.accent)
            }
        }
    }
    
    private func settingDropdown(label: String, description: String, selection: Binding<String>, options: [String]) -> some View {
        VStack(alignment: .leading, spacing: theme.spacingS) {
            Text(label)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(theme.secondaryText)
            
            Text(description)
                .font(.system(size: 12))
                .foregroundColor(theme.tertiaryText)
            
            Menu {
                ForEach(options, id: \.self) { option in
                    Button(option) {
                        selection.wrappedValue = option
                    }
                }
            } label: {
                HStack {
                    Text(selection.wrappedValue)
                        .foregroundColor(theme.primaryText)
                    Spacer()
                    Image(systemName: "chevron.down")
                        .foregroundColor(theme.tertiaryText)
                }
                .font(.system(size: 17))
                .padding(theme.spacingM)
                .background(theme.tertiaryBackground)
                .clipShape(RoundedRectangle(cornerRadius: theme.radiusSmall))
                .overlay(
                    RoundedRectangle(cornerRadius: theme.radiusSmall)
                        .stroke(theme.border, lineWidth: 1)
                )
            }
        }
    }
    
    private func infoRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(theme.secondaryText)
            
            Spacer()
            
            Text(value)
                .font(.system(size: 14))
                .foregroundColor(theme.primaryText)
        }
    }
}

@MainActor
class SettingsViewModel: ObservableObject {
    @Published var portNumber = "5005"
    @Published var autoDiscovery = true
    @Published var verboseLogging = false
    @Published var logRetention = "30 days"
    @Published var handshakeTimeout = "3000"
    @Published var appVersion = "2.0.0"
    @Published var buildNumber = "1"
    @Published var deviceNodeId = UUID().uuidString.prefix(8).uppercased()
    
    let logRetentionOptions = ["7 days", "30 days", "90 days", "Unlimited"]
    
    func loadSettings() async {
        try? await Task.sleep(nanoseconds: 300_000_000)
    }
    
    func saveSettings() async {
        try? await Task.sleep(nanoseconds: 500_000_000)
        print("Settings saved")
    }
    
    func resetToDefaults() {
        portNumber = "5005"
        autoDiscovery = true
        verboseLogging = false
        logRetention = "30 days"
        handshakeTimeout = "3000"
    }
}