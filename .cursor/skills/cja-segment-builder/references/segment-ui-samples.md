# Segment UI Samples

Use these as layout guides when describing or reconstructing CJA segment definitions from the UI.

## Simple visitor rule

```text
Title*: Test segment X
Description: Visitors with Product Name [Data Mirror AZB] = Compression Socks.

Definition*:
Include  Person
  Product Name [Data Mirror AZB]  does not equal  Compression Socks
```

## Single hit rule with verified value

```text
Title*: [MCP lab] Visitors — mobile channel
Description: Visitors with at least one hit where ?Data Source Channel [multi] equals mobile.

Definition*:
Include  Person
  ?Data Source Channel [multi]  equals  mobile
```

## Sequential / nested example

```text
Title*: Everything segment!
Description: Complex sequential visitor segment.

Definition*:
Include  Person
  Then
    Visit
      Event Type [core] equals (Distinct Count) 1
      AND Event Type [core] exists
      AND Event Type [core] equals web.webpagedetails.pageViews
  Exclude next checkpoint
  Hit
    Price Total [multi] is greater than or equal to 1
    OR
    Nested visitor container
      Product Name [Data Mirror AZB] equals Compression Socks
```

## Modifier-heavy example

```text
Title*: Additional segment features
Description: Uses sequence modifiers and negative matches.

Definition*:
Include  Session
  Product Name [multi] does not exist
  Then
    After 3 Product Name [multi]
    But Within 1 Hour(s)
    Platform Dataset ID [core] does not match a*b
```

## Reading the UI

- The top bar usually shows the segment title and optional description.
- The definition area starts with **Include / Exclude** and a scope selector such as **Person**, **Visit**, **Session**, or **Hit**.
- Each row is a predicate.
- Nested containers appear indented and may be separated by sequence controls like **Then**, **Only Before Sequence**, or **Only After**.
- For exact-value predicates, the UI often shows a value picker on the right side of the row.
- Modifiers such as **After**, **Within**, **Does not exist**, and **Does not match** are often rendered as inline chips or dropdown chips around the predicate row.
