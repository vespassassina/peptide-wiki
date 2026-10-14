import Foundation

@main
struct ExportBiometra {
    static func canonicalData(_ data: Data) throws -> Data {
        guard var entries = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw NSError(
                domain: "BiohackerWikiExport", code: 3,
                userInfo: [NSLocalizedDescriptionKey: "Expected a JSON array of catalogue objects."]
            )
        }
        // Weekdays are a Set in the source; array order has no semantic meaning here.
        for index in entries.indices {
            guard var template = entries[index]["template"] as? [String: Any],
                  var recurrence = template["typicalRecurrence"] as? [String: Any],
                  var weekdays = recurrence["weekdays"] as? [String: Any],
                  let days = weekdays["_0"] as? [Int] else { continue }
            weekdays["_0"] = days.sorted()
            recurrence["weekdays"] = weekdays
            template["typicalRecurrence"] = recurrence
            entries[index]["template"] = template
        }
        return try JSONSerialization.data(
            withJSONObject: entries,
            options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        )
    }

    static func main() throws {
        let entries = LibraryCatalog.authoredEntries.sorted { $0.id < $1.id }
        guard Set(entries.map(\.id)).count == entries.count else {
            throw NSError(
                domain: "BiohackerWikiExport", code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Duplicate authored catalogue IDs; fix the source before exporting."]
            )
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        let data = try canonicalData(encoder.encode(entries))
        let decoded = try JSONDecoder().decode([LibraryCatalogEntry].self, from: data)
        guard decoded == entries else {
            throw NSError(
                domain: "BiohackerWikiExport", code: 2,
                userInfo: [NSLocalizedDescriptionKey: "Catalogue Codable round-trip lost values; fix decoding before exporting."]
            )
        }
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
    }
}
