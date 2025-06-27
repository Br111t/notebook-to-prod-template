# src/cli.py
import pandas as pd
from typing import Optional
from .emotion import get_analysis


def analyze_df(df: pd.DataFrame, text_column: str) -> pd.DataFrame:
    """
    Pure function: takes a DataFrame + name of the text column,
    returns a new DataFrame with emotion, concepts & semantic-roles merged in.
    """
    texts = df[text_column].astype(str).tolist()
    df_analysis = get_analysis(texts).drop(columns=["text"])
    return pd.concat([df.reset_index(drop=True), df_analysis], axis=1)


def main(
    input_csv: str,
    text_column: str,
    output_csv: Optional[str] = None
):
    """I/O wrapper: reads CSV, calls analyze_df, writes or prints result."""
    df = pd.read_csv(input_csv)
    df_out = analyze_df(df, text_column)

    if output_csv:
        df_out.to_csv(output_csv, index=False)
        print(f"Wrote analysis to {output_csv}")
    else:
        print(df_out.to_string(index=False))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--input",  "-i", required=True, help="path to input CSV")
    p.add_argument("--column", "-c", required=True, help="text column name")
    p.add_argument("--output", "-o", help="where to write (optional)")
    args = p.parse_args()
    main(args.input, args.column, args.output)
