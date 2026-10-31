import SwiftUI

struct SyncLogsView: View {
    @ObservedObject var theme = ThemeManager.shared
    @StateObject private var viewModel = SyncLogsViewModel()
    @Environment(\.dismiss) var dismiss
    @State private var selectedPeerFilter = "All Peers"
    @State private var selectedStatusFilter = "All Status"
    @State private var expandedLogId: UUID? = nil
    @State private var showClearConfirmation = false
    
    var body: some View {
        ZStack {
            theme.primaryBackground
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                filterSection
                    .padding(.horizontal, theme.spacingL)
                    .padding(.vertical, theme.spacingM)
                    .background(theme.cardBackground)
                
                Divider()
                    .background(theme.divider)
                
                if viewModel.isLoading {
                    loadingView
                } else if viewModel.filteredLogs.isEmpty {
                    emptyLogsState
                } else {
                    logsListView
                }
            }
        }
        .navigationTitle("Sync Logs")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .topBarTrailing) {
                Button {
                    viewModel.exportLogs()
                } label: {
                    Image(systemName: "square.and.arrow.up")
                        .foregroundColor(theme.accent)
                }
                
                Button {
                    showClearConfirmation = true
                } label: {
                    Image(systemName: "trash")
                        .foregroundColor(theme.error)
                }
            }
            
            ToolbarItemGroup(placement: .cancellationAction) {
                Button("Done") {
                    dismiss()
                }
                .foregroundColor(theme.accent)
            }
        }
        .alert("Clear All Logs", isPresented: $showClearConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("Clear", role: .destructive) {
                viewModel.clearLogs()
            }
        } message: {
            Text("Are you sure you want to delete all sync logs? This action cannot be undone.")
        }
        .task {
            await viewModel.loadLogs()
        }
    }
    
    private var filterSection: some View {
        VStack(spacing: theme.spacingM) {
            HStack(spacing: theme.spacingM) {
                Image(systemName: "line.3.horizontal.decrease.circle")
                    .font(.system(size: 20))
                    .foregroundColor(theme.accent)
                
                Text("Filters")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(theme.primaryText)
                
                Spacer()
                
                if viewModel.isRealTimeUpdating {
                    HStack(spacing: 6) {
                        Circle()
                            .fill(theme.success)
                            .frame(width: 8, height: 8)
                        
                        Text("Live")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(theme.success)
                    }
                }
            }
            
            HStack(spacing: theme.spacingM) {
                filterDropdown(
                    title: "Peer",
                    selection: $selectedPeerFilter,
                    options: viewModel.peerFilterOptions
                )
                
                filterDropdown(
                    title: "Status",
                    selection: $selectedStatusFilter,
                    options: viewModel.statusFilterOptions
                )
            }
        }
    }
    
    private func filterDropdown(title: String, selection: Binding<String>, options: [String]) -> some View {
        Menu {
            ForEach(options, id: \.self) { option in
                Button(option) {
                    selection.wrappedValue = option
                    viewModel.applyFilters(peer: selectedPeerFilter, status: selectedStatusFilter)
                }
            }
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(theme.secondaryText)
                    
                    Text(selection.wrappedValue)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(theme.primaryText)
                        .lineLimit(1)
                }
                
                Spacer()
                
                Image(systemName: "chevron.down")
                    .font(.system(size: 12))
                    .foregroundColor(theme.tertiaryText)
            }
            .padding(.horizontal, theme.spacingM)
            .padding(.vertical, theme.spacingS)
            .frame(maxWidth: .infinity)
            .background(theme.tertiaryBackground)
            .clipShape(RoundedRectangle(cornerRadius: theme.radiusSmall))
            .overlay(
                RoundedRectangle(cornerRadius: theme.radiusSmall)
                    .stroke(theme.border, lineWidth: 1)
            )
        }
    }
    
    private var logsListView: some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: theme.spacingM) {
                ForEach(viewModel.filteredLogs) { log in
                    SyncLogCard(log: log, isExpanded: expandedLogId == log.id)
                        .onTapGesture {
                            withAnimation(theme.springSnappy) {
                                expandedLogId = expandedLogId == log.id ? nil : log.id
                            }
                        }
                }
            }
            .padding(.horizontal, theme.spacingL)
            .padding(.vertical, theme.spacingM)
            .padding(.bottom, 100)
        }
    }
    
    private var loadingView: some View {
        VStack(spacing: theme.spacingL) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: theme.accent))
                .scaleEffect(1.2)
            
            Text("Loading logs...")
                .font(.system(size: 14))
                .foregroundColor(theme.secondaryText)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var emptyLogsState: some View {
        VStack(spacing: theme.spacingL) {
            Image(systemName: "doc.text")
                .font(.system(size: 50))
                .foregroundColor(theme.tertiaryText)
            
            Text("No Logs Found")
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(theme.primaryText)
            
            Text("Sync logs will appear here as you connect with peers")
                .font(.system(size: 14))
                .foregroundColor(theme.secondaryText)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, theme.spacingXL)
    }
}

struct SyncLogCard: View {
    @ObservedObject var theme = ThemeManager.shared
    let log: AppSyncLog
    let isExpanded: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacingM) {
            HStack(alignment: .top, spacing: theme.spacingM) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 10, height: 10)
                    .padding(.top, 4)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(log.message ?? "Sync event")
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(theme.primaryText)
                        .lineLimit(isExpanded ? nil : 2)
                    
                    HStack(spacing: theme.spacingS) {
                        if let timestamp = log.timestamp {
                            Text(formatTime(timestamp))
                                .font(.system(size: 12))
                                .foregroundColor(theme.secondaryText)
                        }
                        
                        if let peerIP = log.peerIP {
                            Text("•")
                                .foregroundColor(theme.tertiaryText)
                            
                            Text(peerIP)
                                .font(.system(size: 12))
                                .foregroundColor(theme.secondaryText)
                        }
                        
                        if let taskType = log.taskType {
                            Text("•")
                                .foregroundColor(theme.tertiaryText)
                            
                            Text(taskType)
                                .font(.system(size: 12))
                                .foregroundColor(theme.secondaryText)
                        }
                    }
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    statusBadge
                    
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 12))
                        .foregroundColor(theme.tertiaryText)
                }
            }
            
            if isExpanded {
                Divider()
                    .background(theme.divider)
                
                VStack(alignment: .leading, spacing: theme.spacingS) {
                    if let errorMsg = log.errorMessage {
                        detailRow(label: "Error", value: errorMsg, color: theme.error)
                    }
                    
                    if let payloadSize = log.payloadSize {
                        detailRow(label: "Payload Size", value: "\(payloadSize) bytes")
                    }
                    
                    if let duration = log.syncDuration {
                        detailRow(label: "Duration", value: String(format: "%.2f seconds", duration))
                    }
                }
            }
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
    
    private var statusBadge: some View {
        Text(log.status?.rawValue ?? "PENDING")
            .font(.system(size: 10, weight: .semibold))
            .foregroundColor(statusColor)
            .padding(.horizontal, theme.spacingS)
            .padding(.vertical, 3)
            .background(
                Capsule()
                    .fill(statusColor.opacity(0.15))
            )
    }
    
    private var statusColor: Color {
        switch log.statusColor {
        case "GREEN":
            return theme.success
        case "RED":
            return theme.error
        case "BLUE":
            return theme.info
        default:
            return theme.tertiaryText
        }
    }
    
    private func detailRow(label: String, value: String, color: Color? = nil) -> some View {
        HStack(alignment: .top) {
            Text(label + ":")
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(theme.secondaryText)
            
            Text(value)
                .font(.system(size: 13))
                .foregroundColor(color ?? theme.primaryText)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        formatter.timeStyle = .medium
        return formatter.string(from: date)
    }
}

@MainActor
class SyncLogsViewModel: ObservableObject {
    @Published var allLogs: [AppSyncLog] = []
    @Published var filteredLogs: [AppSyncLog] = []
    @Published var isLoading = false
    @Published var isRealTimeUpdating = true
    @Published var peerFilterOptions = ["All Peers"]
    @Published var statusFilterOptions = ["All Status", "SUCCESS", "FAILED", "PENDING", "ATTEMPT"]
    
    func loadLogs() async {
        isLoading = true
        defer { isLoading = false }
        
        try? await Task.sleep(nanoseconds: 800_000_000)
        
        allLogs = [
            AppSyncLog(
                timestamp: Date(),
                peerIP: "192.168.1.100",
                taskType: "Handshake",
                status: .success,
                message: "Success: Established link with 192.168.1.100",
                payloadSize: 256,
                syncDuration: 0.45
            ),
            AppSyncLog(
                timestamp: Date().addingTimeInterval(-120),
                peerIP: "192.168.1.101",
                taskType: "Model Transfer",
                status: .attempt,
                message: "Syncing Intent: Model Transfer...",
                payloadSize: 1024,
                syncDuration: 0.0
            ),
            AppSyncLog(
                timestamp: Date().addingTimeInterval(-300),
                peerIP: "192.168.1.100",
                taskType: "Data Sync",
                status: .success,
                message: "Data synchronization completed",
                payloadSize: 512,
                syncDuration: 1.2
            ),
            AppSyncLog(
                timestamp: Date().addingTimeInterval(-600),
                peerIP: "192.168.1.102",
                taskType: "Handshake",
                status: .failed,
                message: "Handshake Failed: Connection timeout",
                errorMessage: "The peer did not respond within the timeout period (3000ms)",
                syncDuration: 3.0
            )
        ]
        
        filteredLogs = allLogs
        
        let uniquePeers = Set(allLogs.compactMap { $0.peerIP })
        peerFilterOptions = ["All Peers"] + uniquePeers.sorted()
    }
    
    func applyFilters(peer: String, status: String) {
        var logs = allLogs
        
        if peer != "All Peers" {
            logs = logs.filter { $0.peerIP == peer }
        }
        
        if status != "All Status" {
            logs = logs.filter { $0.status?.rawValue == status }
        }
        
        filteredLogs = logs
    }
    
    func clearLogs() {
        allLogs.removeAll()
        filteredLogs.removeAll()
    }
    
    func exportLogs() {
        print("Exporting logs...")
    }
}