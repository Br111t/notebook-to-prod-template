import pandas as pd
from typing import List, Optional
from .emotion import get_emotions  # Import the get_emotions function from emotion.py

def analyze_csv(
    input_csv: str = "data/input.csv",
    text_column: str = "text",
    output_csv: Optional[str] = None,
) -> pd.DataFrame:
    """
    Reads `input_csv`, extracts `text_column`, runs tone analysis,
    and returns a DataFrame with the original data plus tone columns.

    If `output_csv` is provided, writes the augmented DataFrame to disk.
    """
    # 1) Read your CSV
    df_in = pd.read_csv(input_csv)

    # 2) Pull out the list of texts
    texts: List[str] = df_in[text_column].astype(str).tolist()

    # 3) Run get_emotions on that list
    df_tones = get_emotions(texts)

    # 4) Merge the tone-scores back in (aligning on order)
    #    This will give you a DataFrame with all original columns
    #    plus one column per tone name.
    df_out = pd.concat([df_in.reset_index(drop=True), df_tones.drop(columns=["text"])], axis=1)

    # 5) Optionally write to disk
    if output_csv:
        df_out.to_csv(output_csv, index=False)

    return df_out
