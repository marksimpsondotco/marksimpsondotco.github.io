import Foundation
import CoreGraphics

/// Encapsulates all layout parameters for positioning an image on a printable disc.
struct DiscLayout: Codable, Equatable {

    // MARK: - Image transform
    /// Uniform scale factor (1.0 = image fills the outer disc diameter).
    var scale: Double = 1.0
    /// Horizontal offset in normalised disc-radius units (−1 … +1).
    var offsetX: Double = 0.0
    /// Vertical offset in normalised disc-radius units (−1 … +1).
    var offsetY: Double = 0.0
    /// Rotation in degrees.
    var rotation: Double = 0.0
    /// How the image is mapped to the disc area.
    var fillMode: FillMode = .fill

    // MARK: - Border
    /// Width of the outer border ring in millimetres (0 = no border).
    var borderWidthMM: Double = 0.0
    /// CSS hex colour string, e.g. "#FF0000".
    var borderColorHex: String = "#000000"

    // MARK: - Colour profile
    var embedColorProfile: Bool = true

    // MARK: - Disc geometry constants (Canon TS8300)
    /// Printable outer radius in mm.
    static let outerRadiusMM: Double = 58.0   // 116 mm diameter
    /// Non-printable inner hub radius in mm.
    static let innerRadiusMM: Double = 19.0   // ~38 mm diameter

    // MARK: - Fill mode
    enum FillMode: String, Codable, CaseIterable, Identifiable {
        case fit    = "Fit"
        case fill   = "Fill"
        case stretch = "Stretch"
        var id: String { rawValue }
    }
}

// MARK: - CGColor helpers
import AppKit

extension DiscLayout {
    var borderNSColor: NSColor {
        get { NSColor(hex: borderColorHex) ?? .black }
        set { borderColorHex = newValue.hexString }
    }
}

// MARK: - NSColor hex helpers (internal)
private extension NSColor {
    convenience init?(hex: String) {
        var str = hex.trimmingCharacters(in: .whitespacesAndNewlines)
        if str.hasPrefix("#") { str = String(str.dropFirst()) }
        guard str.count == 6, let value = UInt64(str, radix: 16) else { return nil }
        let r = CGFloat((value >> 16) & 0xFF) / 255
        let g = CGFloat((value >> 8)  & 0xFF) / 255
        let b = CGFloat( value        & 0xFF) / 255
        self.init(sRGBRed: r, green: g, blue: b, alpha: 1)
    }

    var hexString: String {
        guard let color = usingColorSpace(.sRGB) else { return "#000000" }
        let r = Int(color.redComponent   * 255)
        let g = Int(color.greenComponent * 255)
        let b = Int(color.blueComponent  * 255)
        return String(format: "#%02X%02X%02X", r, g, b)
    }
}
