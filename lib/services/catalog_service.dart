import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Represents a gas cylinder product in the catalog.
class Cylinder {
  final String id;
  final String name;
  final double sizeKg;
  final String gasType;
  final double price;
  final String imageUrl;
  final bool inStock;

  /// Named-parameter constructor with all fields required. All fields are final.
  const Cylinder({
    required this.id,
    required this.name,
    required this.sizeKg,
    required this.gasType,
    required this.price,
    required this.imageUrl,
    required this.inStock,
  });

  /// Creates an empty Cylinder with default/placeholder values.
  /// Useful for initializing form state or representing an unset selection.
  const Cylinder.empty()
      : id = '',
        name = '',
        sizeKg = 0.0,
        gasType = '',
        price = 0.0,
        imageUrl = '',
        inStock = false;

  /// Factory constructor. Maps JSON keys to fields.
  /// Casts num to double for sizeKg and price.
  factory Cylinder.fromJson(Map<String, dynamic> json) {
    return Cylinder(
      id: json['id'] as String,
      name: json['name'] as String,
      sizeKg: (json['sizeKg'] as num).toDouble(),
      gasType: json['gasType'] as String,
      price: (json['price'] as num).toDouble(),
      imageUrl: json['imageUrl'] as String,
      inStock: json['inStock'] as bool,
    );
  }

  /// Returns a copy of this Cylinder with the given fields replaced by
  /// non-null values. Fields not provided retain their original values.
  Cylinder copyWith({
    String? id,
    String? name,
    double? sizeKg,
    String? gasType,
    double? price,
    String? imageUrl,
    bool? inStock,
  }) {
    return Cylinder(
      id: id ?? this.id,
      name: name ?? this.name,
      sizeKg: sizeKg ?? this.sizeKg,
      gasType: gasType ?? this.gasType,
      price: price ?? this.price,
      imageUrl: imageUrl ?? this.imageUrl,
      inStock: inStock ?? this.inStock,
    );
  }
}

/// Exception thrown when catalog operations fail.
class CatalogException implements Exception {
  final String message;

  const CatalogException(this.message);

  @override
  String toString() => 'CatalogException: $message';
}

/// Service for fetching the cylinder catalog from the backend API.
class CatalogService {
  final http.Client _client;
  final String _baseUrl;

  /// Creates a CatalogService with optional HTTP client and base URL for
  /// dependency injection and testing.
  CatalogService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ??
            const String.fromEnvironment(
              'API_BASE_URL',
              defaultValue: 'http://localhost:3000',
            );

  /// Performs an HTTP GET to the catalog endpoint and returns a list of
  /// [Cylinder] objects parsed from the JSON response.
  ///
  /// Throws [CatalogException] on HTTP errors, network failures, or
  /// JSON parse failures.
  Future<List<Cylinder>> fetchCatalog() async {
    final http.Response response;

    try {
      response = await _client.get(Uri.parse('$_baseUrl/api/v1/catalog'));
    } on SocketException catch (e) {
      throw CatalogException('Network error: ${e.message}');
    } on TimeoutException catch (e) {
      throw CatalogException('Network error: ${e.message}');
    } catch (e) {
      throw CatalogException('Network error: $e');
    }

    if (response.statusCode != 200) {
      throw CatalogException('HTTP ${response.statusCode}');
    }

    final List<dynamic> jsonList;
    try {
      final dynamic decoded = json.decode(response.body);
      jsonList = decoded as List<dynamic>;
    } on FormatException {
      throw CatalogException('Invalid response format');
    } catch (e) {
      throw CatalogException('Invalid response format');
    }

    try {
      return jsonList
          .map((dynamic item) =>
              Cylinder.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw CatalogException('Invalid catalog data');
    }
  }
}
<<<END_A3_FILE>>>