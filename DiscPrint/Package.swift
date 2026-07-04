// swift-tools-version: 5.9
// Open Package.swift in Xcode (File ▸ Open) to build and run the app.

import PackageDescription

let package = Package(
    name: "DiscPrint",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .executableTarget(
            name: "DiscPrint",
            path: "Sources",
            resources: [
                .process("Resources")
            ]
        )
    ]
)
