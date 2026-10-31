import Foundation

struct AppPeer: Identifiable, Hashable, Codable {
    let id: UUID
    var ipAddress: String?
    var deviceType: String?
    var version: String?
    var status: PeerStatus?
    var lastSyncTime: Date?
    
    enum PeerStatus: String, Codable {
        case connected = "CONNECTED"
        case disconnected = "DISCONNECTED"
    }
    
    init(id: UUID = UUID(), ipAddress: String? = nil, deviceType: String? = nil, version: String? = nil, status: PeerStatus? = .disconnected, lastSyncTime: Date? = nil) {
        self.id = id
        self.ipAddress = ipAddress
        self.deviceType = deviceType
        self.version = version
        self.status = status
        self.lastSyncTime = lastSyncTime
    }
}

struct AppTask: Identifiable, Hashable, Codable {
    let id: UUID
    var taskType: String?
    var status: TaskStatus?
    var payload: String?
    var timestamp: Date?
    var originatingDevice: String?
    var syncProgress: Double?
    
    enum TaskStatus: String, Codable {
        case idle = "IDLE"
        case active = "ACTIVE"
        case synced = "SYNCED"
    }
    
    init(id: UUID = UUID(), taskType: String? = nil, status: TaskStatus? = .idle, payload: String? = nil, timestamp: Date? = nil, originatingDevice: String? = nil, syncProgress: Double? = 0.0) {
        self.id = id
        self.taskType = taskType
        self.status = status
        self.payload = payload
        self.timestamp = timestamp
        self.originatingDevice = originatingDevice
        self.syncProgress = syncProgress
    }
}

struct AppSyncLog: Identifiable, Hashable, Codable {
    let id: UUID
    var timestamp: Date?
    var peerIP: String?
    var taskType: String?
    var status: LogStatus?
    var message: String?
    var errorMessage: String?
    var payloadSize: Int?
    var syncDuration: Double?
    
    enum LogStatus: String, Codable {
        case attempt = "ATTEMPT"
        case success = "SUCCESS"
        case failed = "FAILED"
        case pending = "PENDING"
    }
    
    var statusColor: String {
        switch status {
        case .attempt, .pending:
            return "BLUE"
        case .success:
            return "GREEN"
        case .failed:
            return "RED"
        case .none:
            return "BLUE"
        }
    }
    
    init(id: UUID = UUID(), timestamp: Date? = nil, peerIP: String? = nil, taskType: String? = nil, status: LogStatus? = .pending, message: String? = nil, errorMessage: String? = nil, payloadSize: Int? = nil, syncDuration: Double? = nil) {
        self.id = id
        self.timestamp = timestamp
        self.peerIP = peerIP
        self.taskType = taskType
        self.status = status
        self.message = message
        self.errorMessage = errorMessage
        self.payloadSize = payloadSize
        self.syncDuration = syncDuration
    }
}

struct AppSettings: Codable {
    var portNumber: Int?
    var autoDiscovery: Bool?
    var verboseLogging: Bool?
    var logRetentionDays: Int?
    var handshakeTimeout: Int?
    
    init(portNumber: Int? = 5005, autoDiscovery: Bool? = true, verboseLogging: Bool? = false, logRetentionDays: Int? = 30, handshakeTimeout: Int? = 3000) {
        self.portNumber = portNumber
        self.autoDiscovery = autoDiscovery
        self.verboseLogging = verboseLogging
        self.logRetentionDays = logRetentionDays
        self.handshakeTimeout = handshakeTimeout
    }
}