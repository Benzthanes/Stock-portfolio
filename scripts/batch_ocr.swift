import Foundation
import Vision
import AppKit

// Check command line arguments
let args = CommandLine.arguments
let targetDir = args.count > 1 ? args[1] : "data/screenshots"
let outputPath = args.count > 2 ? args[2] : "data/.ocr_extracted.json"

let fileManager = FileManager.default
let currentPath = fileManager.currentDirectoryPath
let folderURL = URL(fileURLWithPath: targetDir, relativeTo: URL(fileURLWithPath: currentPath)).standardized

var isDir: ObjCBool = false
guard fileManager.fileExists(atPath: folderURL.path, isDirectory: &isDir), isDir.boolValue else {
    fputs("Error: Directory '\(folderURL.path)' does not exist.\n", stderr)
    exit(1)
}

let allowedExtensions = Set(["png", "jpg", "jpeg", "heic", "webp"])
guard let allFiles = try? fileManager.contentsOfDirectory(at: folderURL, includingPropertiesForKeys: nil) else {
    fputs("Error: Cannot read directory contents.\n", stderr)
    exit(1)
}

let imageFiles = allFiles.filter { allowedExtensions.contains($0.pathExtension.lowercased()) }.sorted { $0.lastPathComponent < $1.lastPathComponent }

if imageFiles.isEmpty {
    fputs("No images found in \(folderURL.path)\n", stderr)
    exit(0)
}

fputs("Processing \(imageFiles.count) images via native Apple Vision OCR...\n", stderr)

var results: [[String: Any]] = []

for (index, fileURL) in imageFiles.enumerated() {
    guard let image = NSImage(contentsOf: fileURL),
          let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let cgImage = bitmap.cgImage else {
        fputs("[\(index + 1)/\(imageFiles.count)] Failed to load \(fileURL.lastPathComponent)\n", stderr)
        continue
    }

    var recognizedLines: [String] = []
    let request = VNRecognizeTextRequest { req, err in
        guard let observations = req.results as? [VNRecognizedTextObservation] else { return }
        recognizedLines = observations.compactMap { $0.topCandidates(1).first?.string }
    }
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["th-TH", "en-US"]

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try? handler.perform([request])

    results.append([
        "filename": fileURL.lastPathComponent,
        "path": fileURL.path,
        "lines": recognizedLines
    ])

    fputs("[\(index + 1)/\(imageFiles.count)] OK: \(fileURL.lastPathComponent) (\(recognizedLines.count) lines)\n", stderr)
}

let outURL = URL(fileURLWithPath: outputPath, relativeTo: URL(fileURLWithPath: currentPath)).standardized
if let jsonData = try? JSONSerialization.data(withJSONObject: results, options: [.prettyPrinted]) {
    try? jsonData.write(to: outURL)
    fputs("Completed! Successfully extracted \(results.count) images to \(outURL.path)\n", stderr)
}
