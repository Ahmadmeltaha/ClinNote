import 'package:flutter/material.dart';
import 'package:orchstate/services/catalog_service.dart';

/// Private helper to capitalize the first letter of a string.
String _capitalize(String s) {
  if (s.isEmpty) return s;
  return '${s[0].toUpperCase()}${s.substring(1)}';
}

/// The main catalog screen that displays a scrollable list of gas cylinders.
///
/// Manages loading, error, empty, and success states. Supports pull-to-refresh
/// via [RefreshIndicator].
class CatalogScreen extends StatefulWidget {
  const CatalogScreen({Key? key}) : super(key: key);

  @override
  _CatalogScreenState createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  List<Cylinder>? _cylinders;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadCatalog();
  }

  Future<void> _loadCatalog() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final data = await CatalogService().fetchCatalog();
      setState(() {
        _cylinders = data;
        _isLoading = false;
      });
    } on CatalogException catch (e) {
      setState(() {
        _errorMessage = e.message;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gas Cylinders'),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null) {
      return _buildErrorState();
    }

    if (_cylinders != null && _cylinders!.isEmpty) {
      return _buildEmptyState();
    }

    return _buildCatalogList();
  }

  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64),
          const SizedBox(height: 16),
          Text(
            'Connection Error',
            style: Theme.of(context).textTheme.headline6,
          ),
          const SizedBox(height: 8),
          const Text(
            "Couldn't load cylinders. Pull down to refresh.",
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadCatalog,
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.inventory_2_outlined, size: 64),
          const SizedBox(height: 16),
          Text(
            'No cylinders available',
            style: Theme.of(context).textTheme.headline6,
          ),
          const SizedBox(height: 8),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 32),
            child: Text(
              'We are currently restocking our inventory. Please check back later.',
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCatalogList() {
    return RefreshIndicator(
      onRefresh: _loadCatalog,
      child: ListView.builder(
        itemCount: _cylinders!.length,
        itemBuilder: (context, index) {
          final cylinder = _cylinders![index];
          return CylinderCard(
            cylinder: cylinder,
            onOrder: cylinder.inStock
                ? () => Navigator.pushNamed(
                      context,
                      '/place-order',
                      arguments: cylinder.id,
                    )
                : null,
          );
        },
      ),
    );
  }
}

/// A card widget that displays the details of a single gas cylinder.
///
/// Shows the cylinder image, name with size, gas type, price, and an Order
/// button. Out-of-stock cylinders are rendered with reduced opacity and an
/// 'Unavailable' chip.
class CylinderCard extends StatelessWidget {
  final Cylinder cylinder;
  final VoidCallback? onOrder;

  const CylinderCard({
    Key? key,
    required this.cylinder,
    this.onOrder,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final card = Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        leading: Image.network(
          cylinder.imageUrl,
          width: 48,
          height: 48,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) =>
              const Icon(Icons.propane_tank, size: 48),
        ),
        title: Text('${cylinder.sizeKg}kg ${cylinder.name}'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Gas Type: ${_capitalize(cylinder.gasType)}'),
            Text(
              '\$${cylinder.price.toStringAsFixed(2)}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            if (!cylinder.inStock) ...[
              const SizedBox(height: 4),
              const Chip(
                label: Text('Unavailable'),
                visualDensity: VisualDensity.compact,
              ),
            ],
          ],
        ),
        trailing: ElevatedButton(
          onPressed: onOrder,
          child: const Text('Order'),
        ),
        isThreeLine: true,
      ),
    );

    if (!cylinder.inStock) {
      return Opacity(
        opacity: 0.5,
        child: card,
      );
    }

    return card;
  }
}