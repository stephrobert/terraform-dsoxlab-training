# The situation

Six months ago, the data team copied the web team's machine configuration,
then changed it its own way. Today, a fix made on one side never reaches the
other, and nobody knows which of the two copies is the reference any more.

The technical leadership decides: a single configuration, published as a
versioned module. The data team wants to be able to freeze what it deploys;
the web team, in production, wants the fixes without rewriting anything, and
above all without losing its machines. There are no lessons and no hints in
this exam: it measures what you already know how to do.
