import SwiftUI

struct PeerDetailsView: View {
    @ObservedObject var theme = ThemeManager.shared
    @StateObject private var viewModel: PeerDetailsViewModel
    @Binding var selectedPeer: AppPeer?
    @Environment(\.dismiss) var dismiss
    @Environment(\.horizontalSizeClass) var horizontalSizeClass
    @State private var showSyncDialog = false
    @State private var expandedLogId: UUID? = nil
    
    init(peer: AppPeer, selectedPeer: Binding<AppPeer?>) {
        _viewModel = StateObject(wrappedValue: PeerDetailsViewModel(peer: peer))
        _selectedPeer = selectedPeer
    }
    
    var body: some View {
        ZStack {
            theme.primaryBackground
                .ignoresSafeArea()
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: theme.spacingXL) {
                    peerInfoCard
                    
                    handshakeStatusCard
                    
                    activeTasksSection
                    
                    connectionLogSection
                }
                .padding(.horizontal, theme.spacingL)
                .padding(.top, theme.spacingM)
                .padding(.bottom, 100)
            }
        }
        .navigationTitle("Peer Details")
        .navigationBarTitleDisplayMode(horizontalSizeClass == .regular ? .inline : .large)
        .toolbar {
            if horizontalSizeClass == .compact {
                ToolbarItemGroup(placement: .topBarTrailing) {
                    Button {
                        Task {
                            await viewModel.initiateHandshake()
                        }
                    } label: {
                        Image(systemName: "arrow.triangle.2.circlepath")
                            .foregroundColor(theme.accent)
                    }
                }
            }
        }
        .sheet(isPresented: $showSyncDialog) {
            SyncIntentDialog(viewModel: viewModel)
        }
        .task {
            await viewModel.loadTasks()
        }
    }
    
    private var peerInfoCard: some View {
        VStack(alignment: .leading, spacing: theme.spacingM) {
            HStack {
                Image(systemName: "info.circle")
                    .font(.system(size: 24))
                    .foregroundColor(theme.accent)
                
                Text("Peer Information")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(theme.primaryText)
                
                Spacer()
                
                statusBadge
            }
            
            Divider()
                .background(theme.divider)
            
            VStack(alignment: .leading, spacing: theme.spacingS) {
                infoRow(label: "IP Address", value: viewModel.peer.ipAddress ?? "Unknown")
                infoRow(label: "Device Type", value: viewModel.peer.deviceType ?? "Unknown")
                infoRow(label: "Version", value: viewModel.peer.version ?? "Unknown")
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
    
    private var statusBadge: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(viewModel.peer.status == .connected ? theme.success : theme.error)
                .frame(width: 8, height: 8)
            
            Text(viewModel.peer.status?.rawValue ?? "DISCONNECTED")
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(viewModel.peer.status == .connected ? theme.success : theme.error)
        }
        .padding(.horizontal, theme.spacingM)
        .padding(.vertical, theme.spacingS)
        .background(
            Capsule()
                .fill((viewModel.peer.status == .connected ? theme.success : theme.error).opacity(0.15))
        )
    }
    
    private var handshakeStatusCard: some View {
        VStack(alignment: .leading, spacing: theme.spacingM) {
            HStack {
                Image(systemName: "link")
                    .font(.system(size: 20))
                    .foregroundColor(theme.accent)
                
                Text("Handshake Status")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(theme.primaryText)
                
                Spacer()
            }
            
            Divider()
                .background(theme.divider)
            
            if let lastSync = viewModel.peer.lastSyncTime {
                VStack(alignment: .leading, spacing: theme.spacingS) {
                    infoRow(label: "Last Handshake", value: formatDate(lastSync))
                    infoRow(label: "Status", value: viewModel.handshakeStatus, color: viewModel.handshakeStatus == "SUCCESS" ? theme.success : theme.error)
                }
            } else {
                Text("No handshake attempts yet")
                    .font(.system(size: 14))
                    .foregroundColor(theme.secondaryText)
            }
            
            Button {
                Task {
                    await viewModel.initiateHandshake()
                }
            } label: {
                HStack {
                    Image(systemName: "arrow.triangle.2.circlepath")
                    Text("Initiate Handshake")
                }
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, theme.spacingM)
                .background(
                    RoundedRectangle(cornerRadius: theme.radiusMedium)
                        .fill(theme.accent)
                )
            }
            .disabled(viewModel.isHandshaking)
            .opacity(viewModel.isHandshaking ? 0.6 : 1.0)
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
    
    private var activeTasksSection: some View {
        VStack(alignment: .leading, spacing: theme.spacingL) {
            HStack {
                Text("Active Tasks")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(theme.primaryText)
                
                Spacer()
                
                Button {
                    showSyncDialog = true
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.left.arrow.right")
                        Text("Sync")
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(theme.accent)
                    .padding(.horizontal, theme.spacingM)
                    .padding(.vertical, theme.spacingS)
                    .background(
                        Capsule()
                            .fill(theme.accentSubtle)
                    )
                }
            }
            
            if viewModel.tasks.isEmpty {
                emptyTasksState
            } else {
                ForEach(viewModel.tasks) { task in
                    TaskCard(task: task)
                }
            }
        }
    }
    
    private var emptyTasksState: some View {
        VStack(spacing: theme.spacingM) {
            Image(systemName: "tray")
                .font(.system(size: 40))
                .foregroundColor(theme.tertiaryText)
            
            Text("No Active Tasks")
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(theme.primaryText)
            
            Text("Sync a task to get started")
                .font(.system(size: 13))
                .foregroundColor(theme.secondaryText)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, theme.spacingXXL)
    }
    
    private var connectionLogSection: some View {
        VStack(alignment: .leading, spacing: theme.spacingL) {
            Text("Connection Log")
                .font(.system(size: 20, weight: .semibold))
                .foregroundColor(theme.primaryText)
            
            VStack(spacing: theme.spacingM) {
                ForEach(viewModel.connectionLogs) { log in
                    ConnectionLogRow(log: log, isExpanded: expandedLogId == log.id)
                        .onTapGesture {
                            withAnimation(theme.springSnappy) {
                                expandedLogId = expandedLogId == log.id ? nil : log.id
                            }
                        }
                }
            }
        }
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
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct TaskCard: View {
    @ObservedObject var theme = ThemeManager.shared
    let task: AppTask
    
    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacingM) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(task.taskType ?? "Unknown Task")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(theme.primaryText)
                        .lineLimit(1)
                    
                    Text(task.originatingDevice ?? "Unknown Device")
                        .font(.system(size: 13))
                        .foregroundColor(theme.secondaryText)
                }
                
                Spacer()
                
                taskStatusBadge
            }
            
            if let progress = task.syncProgress, progress > 0 {
                ProgressView(value: progress, total: 1.0)
                    .progressViewStyle(LinearProgressViewStyle(tint: theme.accent))
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
    
    private var taskStatusBadge: some View {
        Text(task.status?.rawValue ?? "IDLE")
            .font(.system(size: 11, weight: .semibold))
            .foregroundColor(statusColor)
            .padding(.horizontal, theme.spacingS)
            .padding(.vertical, 4)
            .background(
                Capsule()
                    .fill(statusColor.opacity(0.15))
            )
    }
    
    private var statusColor: Color {
        switch task.status {
        case .active:
            return theme.info
        case .synced:
            return theme.success
        case .idle, .none:
            return theme.tertiaryText
        }
    }
}

struct ConnectionLogRow: View {
    @ObservedObject var theme = ThemeManager.shared
    let log: AppSyncLog
    let isExpanded: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacingS) {
            HStack(spacing: theme.spacingM) {
                Circle()
                    .fill(logColor)
                    .frame(width: 8, height: 8)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(log.message ?? "Connection event")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(theme.primaryText)
                        .lineLimit(isExpanded ? nil : 1)
                    
                    if let timestamp = log.timestamp {
                        Text(formatTime(timestamp))
                            .font(.system(size: 12))
                            .foregroundColor(theme.secondaryText)
                    }
                }
                
                Spacer()
                
                Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                    .font(.system(size: 12))
                    .foregroundColor(theme.tertiaryText)
            }
            
            if isExpanded, let errorMsg = log.errorMessage {
                Text(errorMsg)
                    .font(.system(size: 13))
                    .foregroundColor(theme.error)
                    .padding(.leading, 20)
            }
        }
        .padding(theme.spacingM)
        .background(
            RoundedRectangle(cornerRadius: theme.radiusMedium)
                .fill(theme.tertiaryBackground)
        )
    }
    
    private var logColor: Color {
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
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct SyncIntentDialog: View {
    @ObservedObject var theme = ThemeManager.shared
    @ObservedObject var viewModel: PeerDetailsViewModel
    @Environment(\.dismiss) var dismiss
    @State private var selectedTaskType = "Data Sync"
    @State private var taskPayload = ""
    
    let taskTypes = ["Data Sync", "Model Transfer", "State Handoff", "Custom Task"]
    
    var body: some View {
        NavigationStack {
            ZStack {
                theme.primaryBackground
                    .ignoresSafeArea()
                
                VStack(spacing: theme.spacingXL) {
                    VStack(alignment: .leading, spacing: theme.spacingS) {
                        Text("Task Type")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(theme.secondaryText)
                        
                        Menu {
                            ForEach(taskTypes, id: \.self) { type in
                                Button(type) {
                                    selectedTaskType = type
                                }
                            }
                        } label: {
                            HStack {
                                Text(selectedTaskType)
                                    .foregroundColor(theme.primaryText)
                                Spacer()
                                Image(systemName: "chevron.down")
                                    .foregroundColor(theme.tertiaryText)
                            }
                            .font(.system(size: 17))
                            .padding(theme.spacingL)
                            .background(theme.tertiaryBackground)
                            .clipShape(RoundedRectangle(cornerRadius: theme.radiusMedium))
                            .overlay(
                                RoundedRectangle(cornerRadius: theme.radiusMedium)
                                    .stroke(theme.border, lineWidth: 1)
                            )
                        }
                    }
                    
                    VStack(alignment: .leading, spacing: theme.spacingS) {
                        Text("Payload (Optional)")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(theme.secondaryText)
                        
                        TextEditor(text: $taskPayload)
                            .font(.system(size: 15))
                            .foregroundColor(theme.primaryText)
                            .frame(height: 120)
                            .padding(theme.spacingM)
                            .background(theme.tertiaryBackground)
                            .clipShape(RoundedRectangle(cornerRadius: theme.radiusMedium))
                            .overlay(
                                RoundedRectangle(cornerRadius: theme.radiusMedium)
                                    .stroke(theme.border, lineWidth: 1)
                            )
                    }
                    
                    Spacer()
                }
                .padding(theme.spacingXL)
            }
            .navigationTitle("Sync Intent")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItemGroup(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundColor(theme.accent)
                }
                
                ToolbarItemGroup(placement: .confirmationAction) {
                    Button("Sync") {
                        Task {
                            await viewModel.syncIntent(taskType: selectedTaskType, payload: taskPayload)
                            dismiss()
                        }
                    }
                    .foregroundColor(theme.accent)
                    .fontWeight(.semibold)
                }
            }
        }
    }
}

@MainActor
class PeerDetailsViewModel: ObservableObject {
    @Published var peer: AppPeer
    @Published var tasks: [AppTask] = []
    @Published var connectionLogs: [AppSyncLog] = []
    @Published var isHandshaking = false
    @Published var handshakeStatus = "SUCCESS"
    
    init(peer: AppPeer) {
        self.peer = peer
    }
    
    func loadTasks() async {
        try? await Task.sleep(nanoseconds: 500_000_000)
        
        tasks = [
            AppTask(
                taskType: "Model Transfer",
                status: .active,
                payload: "AI Model v2.1",
                timestamp: Date(),
                originatingDevice: "iPhone 16",
                syncProgress: 0.65
            ),
            AppTask(
                taskType: "Data Sync",
                status: .synced,
                payload: "User preferences",
                timestamp: Date().addingTimeInterval(-600),
                originatingDevice: "BLU 160",
                syncProgress: 1.0
            )
        ]
        
        connectionLogs = [
            AppSyncLog(
                timestamp: Date().addingTimeInterval(-120),
                peerIP: peer.ipAddress,
                taskType: "Handshake",
                status: .success,
                message: "Connection established successfully",
                syncDuration: 0.45
            ),
            AppSyncLog(
                timestamp: Date().addingTimeInterval(-300),
                peerIP: peer.ipAddress,
                taskType: "Handshake",
                status: .attempt,
                message: "Attempting connection...",
                syncDuration: 0.0
            )
        ]
    }
    
    func initiateHandshake() async {
        isHandshaking = true
        defer { isHandshaking = false }
        
        try? await Task.sleep(nanoseconds: 2_000_000_000)
        
        handshakeStatus = "SUCCESS"
        peer.status = .connected
        peer.lastSyncTime = Date()
        
        let newLog = AppSyncLog(
            timestamp: Date(),
            peerIP: peer.ipAddress,
            taskType: "Handshake",
            status: .success,
            message: "Handshake completed successfully",
            syncDuration: 2.0
        )
        connectionLogs.insert(newLog, at: 0)
    }
    
    func syncIntent(taskType: String, payload: String) async {
        let newTask = AppTask(
            taskType: taskType,
            status: .active,
            payload: payload.isEmpty ? nil : payload,
            timestamp: Date(),
            originatingDevice: "This Device",
            syncProgress: 0.0
        )
        tasks.insert(newTask, at: 0)
        
        let newLog = AppSyncLog(
            timestamp: Date(),
            peerIP: peer.ipAddress,
            taskType: taskType,
            status: .attempt,
            message: "Syncing intent: \(taskType)",
            syncDuration: 0.0
        )
        connectionLogs.insert(newLog, at: 0)
    }
}