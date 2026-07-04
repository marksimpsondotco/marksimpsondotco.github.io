import SwiftUI

@main
struct DiscPrintApp: App {
    @StateObject private var presetStore = PresetStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(presetStore)
                .frame(minWidth: 900, minHeight: 640)
        }
        .windowStyle(.titleBar)
        .windowToolbarStyle(.unified)
        .commands {
            CommandGroup(replacing: .newItem) {}
            CommandMenu("File") {
                Button("Open Image…") {
                    NotificationCenter.default.post(name: .openImage, object: nil)
                }
                .keyboardShortcut("o", modifiers: .command)
            }
        }
    }
}

extension Notification.Name {
    static let openImage = Notification.Name("DiscPrint.openImage")
}
