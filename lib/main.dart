import 'package:flutter/material.dart';
import 'package:orchstate/screens/catalog_screen.dart';

void main() {
  runApp(const OrchStateApp());
}

class OrchStateApp extends StatelessWidget {
  const OrchStateApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'OrchState',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      routes: <String, WidgetBuilder>{
        '/': (BuildContext context) => const CatalogScreen(),
        '/catalog': (BuildContext context) => const CatalogScreen(),
      },
    );
  }
}