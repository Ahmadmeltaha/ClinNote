import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_project_name/src/widgets/ContactForm.dart';
import 'package:mockito/mockito.dart';

// Mocks
class MockApiService extends Mock {
  Future<bool> submitContactForm(Map<String, String> formData);
}

export 'ContactFormTest';

class ContactFormTest {
  void main() {
    group('ContactForm Test', () {
      late MockApiService mockApiService;

      setUp(() {
        mockApiService = MockApiService();
      });

      // Fixture for valid input
      final validInputFixture = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'message': 'This is a test message.'
      };

      // Fixture for invalid input
      final invalidInputFixture = {
        'name': '',
        'email': 'invalid-email',
        'message': ''
      };

      testWidgets('it should submit the form with valid inputs and call the API', (WidgetTester tester) async {
        // Arrange
        when(mockApiService.submitContactForm(validInputFixture)).thenAnswer((_) async => true);

        // Act
        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ContactForm(apiService: mockApiService),
          ),
        ));

        // Fill in the form with valid data
        await tester.enterText(find.byKey(Key('contactName')), validInputFixture['name']);
        await tester.enterText(find.byKey(Key('contactEmail')), validInputFixture['email']);
        await tester.enterText(find.byKey(Key('contactMessage')), validInputFixture['message']);

        // Tap the submit button
        await tester.tap(find.byKey(Key('submitContactButton')));
        await tester.pumpAndSettle();

        // Assert
        verify(mockApiService.submitContactForm(validInputFixture)).called(1);
      });

      testWidgets('it should show an error message when the form is submitted with invalid inputs', (WidgetTester tester) async {
        // Arrange
        when(mockApiService.submitContactForm(invalidInputFixture)).thenAnswer((_) async => false);

        // Act
        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ContactForm(apiService: mockApiService),
          ),
        ));

        // Fill in the form with invalid data
        await tester.enterText(find.byKey(Key('contactName')), invalidInputFixture['name']);
        await tester.enterText(find.byKey(Key('contactEmail')), invalidInputFixture['email']);
        await tester.enterText(find.byKey(Key('contactMessage')), invalidInputFixture['message']);

        // Tap the submit button
        await tester.tap(find.byKey(Key('submitContactButton')));
        await tester.pumpAndSettle();

        // Assert
        expect(find.byType(SnackBar), findsOneWidget);
        expect(find.text('Please fill out all fields correctly.'), findsOneWidget); // Assuming this is the error message
      });
    });
  }
}
