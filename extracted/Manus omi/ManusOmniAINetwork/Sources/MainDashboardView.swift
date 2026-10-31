import SwiftUI

struct MainDashboardView: View {
    @ObservedObject var theme = ThemeManager.shared
    @StateObject private var viewModel = DashboardViewModel()
    @State private var selectedPeer: AppPeer? = nil
    @State private var showAddPeerDialog = false
    @State private var showSettings = false
    @State private var showSyncLogs = false
    @Environment(\.horizontalSizeClass) var horizontalSizeClass
    
    var body: some View {
        Group {
            if horizontalSizeClass == .regular {
                NavigationSplitView {
                    sidebarContent
                } detail: {
                    if let peer = selectedPeer {
                        PeerDetailsView(peer: peer, selectedPeer: $selectedPeer)
                    } else {
                        ContentUnavailableView(
                            "Select a Peer",
                            systemImage: "network",
                            description: Text("Choose a peer from the list to view details")
                        )
                    }
                }
                .navigationSplitViewStyle(.balanced)
            } else {
                NavigationStack {
                    dashboardContent
                        .navigationTitle("Manus Omni")
                        .navigationBarTitleDisplayMode(.large)
                        .toolbar {
                            ToolbarItemGroup(placement: .topBarTrailing) {
                                Button {
                                    showSyncLogs = true
                                } label: {
                                    Image(systemName: "doc.text")
                                        .foregroundColor(theme.accent)
                                }
                                
                                Button {
                                    showSettings = true
                                } label: {
                                    Image(systemName: "gearshape")
                                        .foregroundColor(theme.accent)
                                }
                            }
                        }
                        .sheet(isPresented: $showSyncLogs) {
                            NavigationStack {
                                SyncLogsView()
                            }
                        }
                        .sheet(isPresented: $showSettings) {
                            NavigationStack {
                                SettingsView()
                            }
                        }
                }
            }
        }
        .sheet(isPresented: $showAddPeerDialog) {
            AddPeerDialog(viewModel: viewModel)
        }
        .task {
            await viewModel.loadPeers()
        }
    }
    
    private var sidebarContent: some View {
        List(viewModel.peers, selection: $selectedPeer) { peer in
            PeerRowView(peer: peer)
                .contentShape(Rectangle())
        }
        .navigationTitle("Peers")
        .toolbar {
            ToolbarItemGroup(placement: .topBarTrailing) {
                Button {
                    Task {
                        await viewModel.refreshPeers()
                    }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                
                Button {
                    showAddPeerDialog = true
                } label: {
                    Image(systemName: "plus.circle")
                }
            }
            
            ToolbarItemGroup(placement: .bottomBar) {
                Button {
                    showSyncLogs = true
                } label: {
                    Label("Sync Logs", systemImage: "doc.text")
                }
                
                Spacer()
                
                Button {
                    showSettings = true
                } label: {
                    Label("Settings", systemImage: "gearshape")
                }
            }
        }
        .sheet(isPresented: $showSyncLogs) {
            NavigationStack {
                SyncLogsView()
            }
        }
        .sheet(isPresented: $showSettings) {
            NavigationStack {
                SettingsView()
            }
        }
    }
    
    private var dashboardContent: some View {
        ZStack {
            theme.primaryBackground
                .ignoresSafeArea()
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: theme.spacingXL) {
                    deviceIdentityCard
                    
                    peerDiscoverySection
                }
                .padding(.horizontal, theme.spacingL)
                .padding(.top, theme.spacingM)
                .padding(.bottom, 100)
            }
            .refreshable {
                await viewModel.refreshPeers()
            }
        }
    }
    
    private var deviceIdentityCard: some View {
        VStack(alignment: .leading, spacing: theme.spacingM) {
            HStack {
                Image(systemName: "person.crop.circle.badge.checkmark")
                    .font(.system(size: 24))
                    .foregroundColor(theme.accent)
                
                Text("Device Identity")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(theme.primaryText)
                
                Spacer()
            }
            
            Divider()
                .background(theme.divider)
            
            VStack(alignment: .leading, spacing: theme.spacingS) {
                infoRow(label: "Node ID", value: viewModel.deviceNodeId)
                infoRow(label: "IP Address", value: viewModel.deviceIP)
                infoRow(label: "Status", value: "ACTIVE", color: theme.success)
            }
        }
        .padding(theme.spacingL)
        .background(
            RoundedRectangle(cornerRadius: theme.radiusXL)
                .fill(theme.cardBackground)
                .shadow(color: theme.shadowColor, radius: theme.shadowRadiusMedium, x: 0, y: 8)
        )
        .overlay(
            RoundedRectangle(cornerRadius: theme.radiusXL)
                .stroke(theme.cardBorder, lineWidth: 1)
        )
    }
    
    private var peerDiscoverySection: some View {
        VStack(alignment: .leading, spacing: theme.spacingL) {
            HStack {
                Text("Peer Discovery")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(theme.primaryText)
                
                Spacer()
                
                Button {
                    showAddPeerDialog = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(theme.accent)
                }
                .frame(minWidth: 44, minHeight: 44)
                .contentShape(Rectangle())
                
                Button {
                    Task {
                        await viewModel.refreshPeers()
                    }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 20))
                        .foregroundColor(theme.accent)
                }
                .frame(minWidth: 44, minHeight: 44)
                .contentShape(Rectangle())
            }
            
            if viewModel.isLoading {
                ForEach(0..<3, id: \.self) { _ in
                    ShimmerPeerCard()
                }
            } else if viewModel.peers.isEmpty {
                emptyPeerState
            } else {
                ForEach(viewModel.peers) { peer in
                    NavigationLink(value: peer) {
                        PeerCard(peer: peer)
                    }
                    .buttonStyle(.plain)
                }
                .navigationDestination(for: AppPeer.self) { peer in
                    PeerDetailsView(peer: peer, selectedPeer: .constant(nil))
                }
            }
        }
    }
    
    private var emptyPeerState: some View {
        VStack(spacing: theme.spacingL) {
            Image(systemName: "network.slash")
                .font(.system(size: 50))
                .foregroundColor(theme.tertiaryText)
            
            Text("No Peers Found")
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(theme.primaryText)
            
            Text("Add a peer manually or refresh to discover devices on your network")
                .font(.system(size: 14))
                .foregroundColor(theme.secondaryText)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, theme.spacingXXL)
    }
    
    private func infoRow(label: String, value: String, color: Color? = nil) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(theme.secondaryText)
            
            Spacer()
            
            Text(value)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(color ?? theme.primaryText)
        }
    }
}

struct PeerRowView: View {
    @ObservedObject var theme = ThemeManager.shared
    let peer: AppPeer
    
    var body: some View {
        HStack(spacing: theme.spacingM) {
            Image(systemName: peer.status == .connected ? "circle.fill" : "circle")
                .font(.system(size: 12))
                .foregroundColor(peer.status == .connected ? theme.success : theme.tertiaryText)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(peer.ipAddress ?? "Unknown IP")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(theme.primaryText)
                
                if let lastSync = peer.lastSyncTime {
                    Text("Last sync: \(formatDate(lastSync))")
                        .font(.system(size: 12))
                        .foregroundColor(theme.secondaryText)
                }
            }
            
            Spacer()
        }
        .padding(.vertical, 8)
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

struct PeerCard: View {
    @ObservedObject var theme = ThemeManager.shared
    let peer: AppPeer
    
    var body: some View {
        HStack(alignment: .center, spacing: theme.spacingL) {
            ZStack {
                RoundedRectangle(cornerRadius: theme.radiusMedium)
                    .fill(peer.status == .connected ? theme.success.opacity(0.15) : theme.tertiaryBackground)
                    .frame(width: 56, height: 56)
                
                Image(systemName: peer.status == .connected ? "network" : "network.slash")
                    .font(.system(size: 24))
                    .foregroundColor(peer.status == .connected ? theme.success : theme.tertiaryText)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(peer.ipAddress ?? "Unknown IP")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(theme.primaryText)
                    .lineLimit(1)
                
                HStack(spacing: theme.spacingS) {
                    Text(peer.status?.rawValue ?? "DISCONNECTED")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(peer.status == .connected ? theme.success : theme.error)
                    
                    if let lastSync = peer.lastSyncTime {
                        Text("•")
                            .foregroundColor(theme.tertiaryText)
                        
                        Text(formatDate(lastSync))
                            .font(.system(size: 14))
                            .foregroundColor(theme.secondaryText)
                    }
                }
            }
            
            Spacer(minLength: 8)
            
            Image(systemName: "chevron.right")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(theme.tertiaryText)
        }
        .padding(theme.spacingL)
        .background(
            RoundedRectangle(cornerRadius: theme.radiusXL)
                .fill(theme.cardBackground)
                .shadow(color: theme.shadowColor, radius: theme.shadowRadiusSmall, x: 0, y: 4)
        )
        .overlay(
            RoundedRectangle(cornerRadius: theme.radiusXL)
                .stroke(theme.cardBorder, lineWidth: 1)
        )
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

struct ShimmerPeerCard: View {
    @ObservedObject var theme = ThemeManager.shared
    
    var body: some View {
        HStack(alignment: .center, spacing: theme.spacingL) {
            ShimmerView()
                .frame(width: 56, height: 56)
                .clipShape(RoundedRectangle(cornerRadius: theme.radiusMedium))
            
            VStack(alignment: .leading, spacing: 6) {
                ShimmerView()
                    .frame(height: 17)
                    .frame(maxWidth: .infinity)
                    .clipShape(RoundedRectangle(cornerRadius: 4))
                
                ShimmerView()
                    .frame(width: 120, height: 14)
                    .clipShape(RoundedRectangle(cornerRadius: 4))
            }
        }
        .padding(theme.spacingL)
        .background(
            RoundedRectangle(cornerRadius: theme.radiusXL)
                .fill(theme.cardBackground)
        )
        .overlay(
            RoundedRectangle(cornerRadius: theme.radiusXL)
                .stroke(theme.cardBorder, lineWidth: 1)
        )
    }
}

struct ShimmerView: View {
    @ObservedObject var theme = ThemeManager.shared
    @State private var isAnimating = false
    
    var body: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [
                        theme.tertiaryBackground,
                        theme.tertiaryBackground.opacity(0.6),
                        theme.tertiaryBackground
                    ],
                    startPoint: isAnimating ? .leading : .trailing,
                    endPoint: isAnimating ? .trailing : .leading
                )
            )
            .onAppear {
                withAnimation(Animation.linear(duration: 1.5).repeatForever(autoreverses: false)) {
                    isAnimating = true
                }
            }
    }
}

struct AddPeerDialog: View {
    @ObservedObject var theme = ThemeManager.shared
    @ObservedObject var viewModel: DashboardViewModel
    @Environment(\.dismiss) var dismiss
    @State private var ipAddress = ""
    @State private var showError = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationStack {
            ZStack {
                theme.primaryBackground
                    .ignoresSafeArea()
                
                VStack(spacing: theme.spacingXL) {
                    VStack(alignment: .leading, spacing: theme.spacingS) {
                        Text("IP Address")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(theme.secondaryText)
                        
                        TextField("192.168.1.100", text: $ipAddress)
                            .font(.system(size: 17))
                            .foregroundColor(theme.primaryText)
                            .padding(theme.spacingL)
                            .background(theme.tertiaryBackground)
                            .clipShape(RoundedRectangle(cornerRadius: theme.radiusMedium))
                            .overlay(
                                RoundedRectangle(cornerRadius: theme.radiusMedium)
                                    .stroke(theme.border, lineWidth: 1)
                            )
                            .keyboardType(.decimalPad)
                    }
                    
                    Spacer()
                }
                .padding(theme.spacingXL)
            }
            .navigationTitle("Add Peer")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItemGroup(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundColor(theme.accent)
                }
                
                ToolbarItemGroup(placement: .confirmationAction) {
                    Button("Add") {
                        addPeer()
                    }
                    .foregroundColor(theme.accent)
                    .fontWeight(.semibold)
                    .disabled(ipAddress.isEmpty)
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    private func addPeer() {
        guard !ipAddress.isEmpty else {
            errorMessage = "Please enter an IP address"
            showError = true
            return
        }
        
        Task {
            await viewModel.addPeer(ipAddress: ipAddress)
            dismiss()
        }
    }
}

@MainActor
class DashboardViewModel: ObservableObject {
    @Published var peers: [AppPeer] = []
    @Published var isLoading = false
    @Published var deviceNodeId = UUID().uuidString.prefix(8).uppercased()
    @Published var deviceIP = "192.168.1.50"
    
    func loadPeers() async {
        isLoading = true
        defer { isLoading = false }
        
        try? await Task.sleep(nanoseconds: 1_000_000_000)
        
        peers = [
            AppPeer(
                ipAddress: "192.168.1.100",
                deviceType: "iPhone 16",
                version: "2.0.0",
                status: .connected,
                lastSyncTime: Date().addingTimeInterval(-300)
            ),
            AppPeer(
                ipAddress: "192.168.1.101",
                deviceType: "BLU 160",
                version: "2.0.0",
                status: .disconnected,
                lastSyncTime: Date().addingTimeInterval(-3600)
            )
        ]
    }
    
    func refreshPeers() async {
        await loadPeers()
    }
    
    func addPeer(ipAddress: String) async {
        let newPeer = AppPeer(
            ipAddress: ipAddress,
            deviceType: "Unknown",
            version: "2.0.0",
            status: .disconnected,
            lastSyncTime: nil
        )
        peers.append(newPeer)
    }
}