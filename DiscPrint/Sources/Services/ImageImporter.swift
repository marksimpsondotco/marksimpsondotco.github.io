import AppKit
import UniformTypeIdentifiers

/// Handles file-open dialogs and drag-and-drop image loading.
final class ImageImporter: ObservableObject {

    static let supportedTypes: [UTType] = [
        .jpeg, .png, .tiff, .bmp, .gif, .heic,
        .rawImage,
        UTType("org.webmproject.webp") ?? .image
    ]

    // MARK: - File open panel

    /// Presents an NSOpenPanel and returns the loaded NSImage, or nil if cancelled / failed.
    @MainActor
    func openImagePanel() async -> NSImage? {
        let panel = NSOpenPanel()
        panel.title = "Choose an Image"
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.allowedContentTypes = Self.supportedTypes

        let response = await panel.beginSheetModal(for: NSApp.keyWindow ?? NSWindow())
        guard response == .OK, let url = panel.url else { return nil }
        return load(from: url)
    }

    // MARK: - URL loading

    func load(from url: URL) -> NSImage? {
        NSImage(contentsOf: url)
    }

    // MARK: - Drag-and-drop helpers

    /// Returns an NSImage from the first compatible item in a drop session.
    func image(fromDrop providers: [NSItemProvider]) async -> NSImage? {
        for provider in providers {
            for type in Self.supportedTypes {
                if provider.hasItemConformingToTypeIdentifier(type.identifier) {
                    if let image = await loadItem(provider: provider, typeIdentifier: type.identifier) {
                        return image
                    }
                }
            }
        }
        return nil
    }

    private func loadItem(provider: NSItemProvider, typeIdentifier: String) async -> NSImage? {
        await withCheckedContinuation { continuation in
            provider.loadItem(forTypeIdentifier: typeIdentifier, options: nil) { item, _ in
                if let url = item as? URL, let image = NSImage(contentsOf: url) {
                    continuation.resume(returning: image)
                } else if let data = item as? Data, let image = NSImage(data: data) {
                    continuation.resume(returning: image)
                } else {
                    continuation.resume(returning: nil)
                }
            }
        }
    }
}
