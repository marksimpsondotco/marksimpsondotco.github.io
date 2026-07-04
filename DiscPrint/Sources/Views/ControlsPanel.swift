import SwiftUI
import AppKit

/// Right-hand panel: all controls for adjusting the disc layout.
struct ControlsPanel: View {
    @Binding var layout: DiscLayout
    let image: NSImage?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                sectionHeader("Fill Mode")
                fillModePicker

                Divider()

                sectionHeader("Transform")
                transformControls

                Divider()

                sectionHeader("Border")
                borderControls

                Divider()

                sectionHeader("Colour Profile")
                Toggle("Embed ICC colour profile", isOn: $layout.embedColorProfile)
                    .toggleStyle(.switch)

                Divider()

                sectionHeader("Position")
                positionNudge

                Spacer(minLength: 20)

                Button("Reset to Defaults") {
                    layout = DiscLayout()
                }
                .frame(maxWidth: .infinity)
            }
            .padding()
        }
        .background(Color(nsColor: .controlBackgroundColor))
    }

    // MARK: - Fill mode

    private var fillModePicker: some View {
        Picker("", selection: $layout.fillMode) {
            ForEach(DiscLayout.FillMode.allCases) { mode in
                Text(mode.rawValue).tag(mode)
            }
        }
        .pickerStyle(.segmented)
        .labelsHidden()
    }

    // MARK: - Transform

    private var transformControls: some View {
        Group {
            labeledSlider("Scale", value: $layout.scale, range: 0.1...4.0, format: "%.2f×")
            labeledSlider("Rotation", value: $layout.rotation, range: -180...180, format: "%.0f°")
        }
    }

    // MARK: - Border

    private var borderControls: some View {
        VStack(alignment: .leading, spacing: 10) {
            labeledSlider("Width", value: $layout.borderWidthMM, range: 0...10, format: "%.1f mm")

            HStack {
                Text("Colour")
                    .frame(width: 80, alignment: .leading)
                    .font(.subheadline)
                ColorPicker("", selection: Binding(
                    get: { Color(nsColor: layout.borderNSColor) },
                    set: { layout.borderColorHex = NSColor($0).hexString }
                ))
                .labelsHidden()
                Spacer()
            }
        }
    }

    // MARK: - Position nudge

    private var positionNudge: some View {
        VStack(spacing: 8) {
            labeledSlider("X offset", value: $layout.offsetX, range: -1...1, format: "%.2f")
            labeledSlider("Y offset", value: $layout.offsetY, range: -1...1, format: "%.2f")

            HStack(spacing: 6) {
                Text("Nudge")
                    .font(.subheadline)
                    .frame(width: 80, alignment: .leading)
                nudgeButton("↑") { layout.offsetY = (layout.offsetY + 0.02).clamped(to: -1...1) }
                nudgeButton("↓") { layout.offsetY = (layout.offsetY - 0.02).clamped(to: -1...1) }
                nudgeButton("←") { layout.offsetX = (layout.offsetX - 0.02).clamped(to: -1...1) }
                nudgeButton("→") { layout.offsetX = (layout.offsetX + 0.02).clamped(to: -1...1) }
                Spacer()
            }
        }
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.headline)
            .padding(.top, 4)
    }

    private func labeledSlider(
        _ label: String,
        value: Binding<Double>,
        range: ClosedRange<Double>,
        format: String
    ) -> some View {
        HStack {
            Text(label)
                .frame(width: 80, alignment: .leading)
                .font(.subheadline)
            Slider(value: value, in: range)
            Text(String(format: format, value.wrappedValue))
                .monospacedDigit()
                .frame(width: 52, alignment: .trailing)
                .font(.caption)
        }
    }

    private func nudgeButton(_ label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .frame(width: 28, height: 24)
        }
        .buttonStyle(.bordered)
        .font(.system(size: 12))
    }
}

// MARK: - NSColor hex helper (for ColorPicker binding)

private extension NSColor {
    var hexString: String {
        guard let c = usingColorSpace(.sRGB) else { return "#000000" }
        return String(format: "#%02X%02X%02X",
                      Int(c.redComponent * 255),
                      Int(c.greenComponent * 255),
                      Int(c.blueComponent * 255))
    }
}
