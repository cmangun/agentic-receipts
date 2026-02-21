# Canonicalization Rules

## Rules

1. **Key ordering**: Object keys sorted lexicographically (Unicode code point order)
2. **Whitespace**: No insignificant whitespace (compact JSON)
3. **Numbers**: No trailing zeros; integers without decimal points
4. **Strings**: UTF-8 encoded, no BOM
5. **Null handling**: Null values included; missing keys excluded
6. **Arrays**: Order preserved

See `vectors/v1/canonicalization_cases.json` for test cases.
