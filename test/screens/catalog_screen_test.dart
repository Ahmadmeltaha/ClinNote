import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '@/screens/catalog_screen.dart';
import '@/services/catalog_service.dart';

/// Mock implementation of [CatalogService] for testing.
/// Delegates [fetchCatalog] to a configurable function so each test can
/// control whether the service returns data, returns empty, or throws.
class MockCatalogService extends CatalogService {
  final Future<List<Cylinder>> Function() fetchCatalogFn;

  MockCatalogService({required this.fetchCatalogFn}) : super();

  @override
  Future<List<Cylinder>> fetchCatalog() => fetchCatalogFn();
}

void main() {
  // ── Fixture data ──────────────────────────────────────────────────────
  const cylinder1 = Cylinder(
    id: 'c1',
    name: 'Propane 11kg',
    sizeKg: 11.0,
    gasType: 'Propane',
    price: 45.00,
    imageUrl: 'https://example.com/c1.png',
    inStock: true,
  );

  const cylinder2 = Cylinder(
    id: 'c2',
    name: 'Butane 15kg',
    sizeKg: 15.0,
    gasType: 'Butane',
    price: 55.00,
    imageUrl: 'https://example.com/c2.png',
    inStock: true,
  );

  const cylinder3 = Cylinder(
    id: 'c3',
    name: 'Propane 45kg',
    sizeKg: 45.0,
    gasType: 'Propane',
    price: 120.00,
    imageUrl: 'https://example.com/c3.png',
    inStock: false,
  );

  // ── Helper to build the widget under test ─────────────────────────────
  Widget buildTestWidget({
    required CatalogService catalogService,
    RouteFactory? onGenerateRoute,
  }) {
    return MaterialApp(
      home: CatalogScreen(catalogService: catalogService),
      onGenerateRoute: onGenerateRoute,
    );
  }

  // ── Tests ─────────────────────────────────────────────────────────────
  group('CatalogScreen', () {
    testWidgets(
      'renders 3 CylinderCards with correct name, sizeKg, gasType, and currency-formatted price',
      (WidgetTester tester) async {
        final mockService = MockCatalogService(
          fetchCatalogFn: () async => <Cylinder>[cylinder1, cylinder2, cylinder3],
        );

        await tester.pumpWidget(
          buildTestWidget(catalogService: mockService),
        );
        await tester.pumpAndSettle();

        // All three CylinderCard widgets are rendered
        expect(find.byType(CylinderCard), findsNWidgets(3));

        // Cylinder 1 — name + size in title
        expect(find.text('11.0kg Propane 11kg'), findsOneWidget);
        // Cylinder 1 — currency-formatted price
        expect(find.text('\$45.00'), findsOneWidget);

        // Cylinder 2 — name + size in title
        expect(find.text('15.0kg Butane 15kg'), findsOneWidget);
        // Cylinder 2 — currency-formatted price
        expect(find.text('\$55.00'), findsOneWidget);

        // Cylinder 3 — name + size in title
        expect(find.text('45.0kg Propane 45kg'), findsOneWidget);
        // Cylinder 3 — currency-formatted price
        expect(find.text('\$120.00'), findsOneWidget);

        // Gas type labels (Propane appears on c1 and c3; Butane on c2)
        expect(find.text('Gas Type: Propane'), findsNWidgets(2));
        expect(find.text('Gas Type: Butane'), findsOneWidget);
      },
    );

    testWidgets(
      'out-of-stock CylinderCard has Opacity 0.5, Unavailable tag, and disabled Order button',
      (WidgetTester tester) async {
        final mockService = MockCatalogService(
          fetchCatalogFn: () async => <Cylinder>[cylinder1, cylinder2, cylinder3],
        );

        await tester.pumpWidget(
          buildTestWidget(catalogService: mockService),
        );
        await tester.pumpAndSettle();

        // The out-of-stock card is wrapped in Opacity with opacity 0.5
        final opacityFinder = find.byWidgetPredicate(
          (Widget widget) => widget is Opacity && widget.opacity == 0.5,
        );
        expect(opacityFinder, findsOneWidget);

        // 'Unavailable' chip / text is displayed on the out-of-stock card
        expect(find.text('Unavailable'), findsOneWidget);

        // The Order button inside the out-of-stock card is disabled (onPressed is null)
        final disabledButtonFinder = find.descendant(
          of: opacityFinder,
          matching: find.byType(ElevatedButton),
        );
        final ElevatedButton button =
            tester.widget<ElevatedButton>(disabledButtonFinder);
        expect(button.onPressed, isNull);
      },
    );

    testWidgets(
      'displays "No cylinders available" title and body text when catalog is empty',
      (WidgetTester tester) async {
        final mockService = MockCatalogService(
          fetchCatalogFn: () async => <Cylinder>[],
        );

        await tester.pumpWidget(
          buildTestWidget(catalogService: mockService),
        );
        await tester.pumpAndSettle();

        // Empty-state title
        expect(find.text('No cylinders available'), findsOneWidget);

        // Empty-state body text
        expect(
          find.text(
            'We are currently restocking our inventory. Please check back later.',
          ),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'displays "Connection Error" title and Retry button when fetchCatalog throws CatalogException',
      (WidgetTester tester) async {
        final mockService = MockCatalogService(
          fetchCatalogFn: () async => throw CatalogException('Network error'),
        );

        await tester.pumpWidget(
          buildTestWidget(catalogService: mockService),
        );
        await tester.pumpAndSettle();

        // Error-state title
        expect(find.text('Connection Error'), findsOneWidget);

        // Retry button is present
        expect(find.text('Retry'), findsOneWidget);
      },
    );

    testWidgets(
      'navigates to /place-order with cylinder ID when Order button is tapped on an in-stock card',
      (WidgetTester tester) async {
        final mockService = MockCatalogService(
          fetchCatalogFn: () async => <Cylinder>[cylinder1, cylinder2, cylinder3],
        );

        RouteSettings? capturedRouteSettings;

        await tester.pumpWidget(
          buildTestWidget(
            catalogService: mockService,
            onGenerateRoute: (RouteSettings settings) {
              capturedRouteSettings = settings;
              return MaterialPageRoute<void>(
                builder: (BuildContext context) => const Scaffold(
                  body: Text('Order Page'),
                ),
                settings: settings,
              );
            },
          ),
        );
        await tester.pumpAndSettle();

        // Tap the Order button on the first in-stock card (cylinder1, id 'c1').
        // find.text('Order') matches all three cards; .first selects cylinder1's button.
        await tester.tap(find.text('Order').first);
        await tester.pumpAndSettle();

        // Verify the pushed route
        expect(capturedRouteSettings, isNotNull);
        expect(capturedRouteSettings!.name, '/place-order');
        expect(capturedRouteSettings!.arguments, 'c1');
      },
    );
  });
}