const compactCurrencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const preciseCurrencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percentFormatter = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const signedPercentFormatter = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: "always",
});

const signedNumberFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
  signDisplay: "always",
});

const numberFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});

const dateTimeFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

export function formatCurrency(value: number | null, compact = false): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  if (compact && Math.abs(value) >= 1000) {
    return compactCurrencyFormatter.format(value);
  }
  return currencyFormatter.format(value);
}

export function formatPreciseCurrency(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return preciseCurrencyFormatter.format(value);
}

export function formatSignedCurrency(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  const formatted = preciseCurrencyFormatter.format(Math.abs(value));
  return value > 0 ? `+${formatted}` : value < 0 ? `-${formatted}` : formatted;
}

export function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return percentFormatter.format(value);
}

export function formatSignedPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return signedPercentFormatter.format(value);
}

export function formatNumber(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return numberFormatter.format(value);
}

export function formatSignedNumber(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return signedNumberFormatter.format(value);
}

export function formatDate(value: string | null): string {
  if (!value) {
    return "--";
  }
  return dateFormatter.format(new Date(value));
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return "--";
  }
  return dateTimeFormatter.format(new Date(value));
}
