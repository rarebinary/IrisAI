import AppKit
import Foundation
import Vision

struct TextObservation: Codable {
    let text: String
    let confidence: Float
    let box: [Double]
}

guard CommandLine.arguments.count == 2 else {
    fputs("Usage: macos_vision_ocr <image-path>\n", stderr)
    exit(2)
}

let imagePath = CommandLine.arguments[1]
guard
    let image = NSImage(contentsOfFile: imagePath),
    let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil)
else {
    fputs("Could not load image at \(imagePath)\n", stderr)
    exit(3)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = ["en-US"]

do {
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try handler.perform([request])
} catch {
    fputs("Vision OCR failed: \(error)\n", stderr)
    exit(4)
}

let width = Double(cgImage.width)
let height = Double(cgImage.height)
let observations = (request.results ?? []).compactMap { observation -> TextObservation? in
    guard let candidate = observation.topCandidates(1).first else {
        return nil
    }

    let bounds = observation.boundingBox
    return TextObservation(
        text: candidate.string,
        confidence: candidate.confidence,
        box: [
            bounds.minX * width,
            (1.0 - bounds.maxY) * height,
            bounds.width * width,
            bounds.height * height,
        ]
    )
}

let encoder = JSONEncoder()
let payload = try encoder.encode(observations)
FileHandle.standardOutput.write(payload)
