import AppKit
import Foundation

/// Manages persisting and loading named layout presets.
final class PresetStore: ObservableObject {

    @Published private(set) var presets: [Preset] = []

    private let fileURL: URL = {
        let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = support.appendingPathComponent("DiscPrint", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("presets.json")
    }()

    init() {
        load()
    }

    // MARK: - CRUD

    func save(preset: Preset) {
        if let idx = presets.firstIndex(where: { $0.id == preset.id }) {
            presets[idx] = preset
        } else {
            presets.append(preset)
        }
        persist()
    }

    func delete(preset: Preset) {
        presets.removeAll { $0.id == preset.id }
        persist()
    }

    func delete(atOffsets offsets: IndexSet) {
        presets.remove(atOffsets: offsets)
        persist()
    }

    // MARK: - Persistence

    private func persist() {
        do {
            let data = try JSONEncoder().encode(presets)
            try data.write(to: fileURL, options: .atomic)
        } catch {
            print("[PresetStore] Failed to save: \(error)")
        }
    }

    private func load() {
        guard let data = try? Data(contentsOf: fileURL) else { return }
        if let decoded = try? JSONDecoder().decode([Preset].self, from: data) {
            presets = decoded
        }
    }
}
