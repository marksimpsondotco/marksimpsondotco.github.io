import SwiftUI
import AppKit

/// The main application window: sidebar (presets) + disc canvas + controls panel.
struct ContentView: View {
    @EnvironmentObject private var presetStore: PresetStore
    @StateObject private var importer = ImageImporter()

    @State private var sourceImage: NSImage?
    @State private var layout = DiscLayout()
    @State private var isDropTargeted = false
    @State private var showPresetSheet = false
    @State private var newPresetName = ""
    @State private var showExportPanel = false
    @State private var printerWarning: String?

    var body: some View {
        NavigationSplitView {
            presetsSidebar
        } detail: {
            HStack(spacing: 0) {
                canvasArea
                Divider()
                ControlsPanel(layout: $layout, image: sourceImage)
                    .frame(width: 260)
            }
            .toolbar { toolbarContent }
        }
        .alert("Printer Warning", isPresented: Binding(
            get: { printerWarning != nil },
            set: { if !$0 { printerWarning = nil } }
        )) {
            Button("OK") { printerWarning = nil }
        } message: {
            Text(printerWarning ?? "")
        }
        .onReceive(NotificationCenter.default.publisher(for: .openImage)) { _ in
            Task { await openImage() }
        }
        .sheet(isPresented: $showPresetSheet) {
            savePresetSheet
        }
    }

    // MARK: - Presets sidebar

    private var presetsSidebar: some View {
        List {
            Section("Presets") {
                if presetStore.presets.isEmpty {
                    Text("No saved presets")
                        .foregroundStyle(.secondary)
                        .font(.caption)
                }
                ForEach(presetStore.presets) { preset in
                    Button {
                        layout = preset.layout
                    } label: {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(preset.name).font(.body)
                            Text(preset.createdAt.formatted(date: .abbreviated, time: .omitted))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .buttonStyle(.plain)
                    .contextMenu {
                        Button("Delete", role: .destructive) {
                            presetStore.delete(preset: preset)
                        }
                    }
                }
                .onDelete { presetStore.delete(atOffsets: $0) }
            }
        }
        .navigationSplitViewColumnWidth(min: 160, ideal: 180)
    }

    // MARK: - Canvas

    private var canvasArea: some View {
        ZStack {
            Color(nsColor: .windowBackgroundColor)

            if let image = sourceImage {
                DiscCanvasView(image: image, layout: $layout)
                    .padding(32)
            } else {
                dropZone
            }
        }
        .onDrop(of: ImageImporter.supportedTypes, isTargeted: $isDropTargeted) { providers in
            Task {
                if let img = await importer.image(fromDrop: providers.map { $0 as NSItemProvider }) {
                    sourceImage = img
                }
            }
            return true
        }
        .overlay(isDropTargeted ? RoundedRectangle(cornerRadius: 8).stroke(Color.accentColor, lineWidth: 3) : nil)
    }

    private var dropZone: some View {
        VStack(spacing: 12) {
            Image(systemName: "opticaldisc")
                .font(.system(size: 56))
                .foregroundStyle(.secondary)
            Text("Drop an image here")
                .font(.title2)
                .foregroundStyle(.secondary)
            Button("Open Image…") {
                Task { await openImage() }
            }
            .controlSize(.large)
        }
    }

    // MARK: - Toolbar

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Button {
                guard let image = sourceImage else { return }
                PrintManager.print(image: image, layout: layout, in: NSApp.keyWindow)
            } label: {
                Label("Print", systemImage: "printer")
            }
            .disabled(sourceImage == nil)
            .help("Print disc")
        }
        ToolbarItem {
            Button {
                Task { await openImage() }
            } label: {
                Label("Open Image", systemImage: "photo.badge.plus")
            }
            .help("Open an image file")
        }
        ToolbarItem {
            Button {
                showPresetSheet = true
            } label: {
                Label("Save Preset", systemImage: "star.badge.plus")
            }
            .disabled(sourceImage == nil)
            .help("Save current layout as a preset")
        }
        ToolbarItem {
            Button {
                exportImage()
            } label: {
                Label("Export", systemImage: "square.and.arrow.up")
            }
            .disabled(sourceImage == nil)
            .help("Export composited disc image")
        }
    }

    // MARK: - Save Preset Sheet

    private var savePresetSheet: some View {
        VStack(spacing: 16) {
            Text("Save Preset").font(.headline)
            TextField("Preset name", text: $newPresetName)
                .textFieldStyle(.roundedBorder)
                .frame(width: 280)
            HStack {
                Button("Cancel") {
                    showPresetSheet = false
                    newPresetName = ""
                }
                Button("Save") {
                    let preset = Preset(name: newPresetName.isEmpty ? "Untitled" : newPresetName,
                                        layout: layout)
                    presetStore.save(preset: preset)
                    showPresetSheet = false
                    newPresetName = ""
                }
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(24)
    }

    // MARK: - Actions

    private func openImage() async {
        if let img = await importer.openImagePanel() {
            sourceImage = img
        }
    }

    private func exportImage() {
        guard let source = sourceImage else { return }
        guard let rendered = PrintManager.renderDiscImage(image: source, layout: layout, dpi: 300) else { return }

        let panel = NSSavePanel()
        panel.title = "Export Disc Image"
        panel.allowedContentTypes = [.png]
        panel.nameFieldStringValue = "disc-print.png"
        guard panel.runModal() == .OK, let url = panel.url else { return }

        guard let tiff = rendered.tiffRepresentation,
              let rep  = NSBitmapImageRep(data: tiff),
              let data = rep.representation(using: .png, properties: [:]) else { return }
        try? data.write(to: url, options: .atomic)
    }
}
