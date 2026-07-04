import Foundation

/// A named saved layout configuration.
struct Preset: Codable, Identifiable, Equatable {
    var id: UUID = UUID()
    var name: String
    var layout: DiscLayout
    var createdAt: Date = Date()
}
