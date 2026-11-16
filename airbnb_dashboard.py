# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair==6.3.0",
#     "marimo>=0.25.2",
#     "numpy==2.5.5",
#     "openpyxl==3.1.5",
#     "pandas==3.1.1",
#     "pingouin==0.7.0",
#     "scipy==1.18.1",
#     "statsmodels==0.15.0",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import numpy as np
    import pingouin as pg

    return alt, mo, np, pd, pg


@app.cell
def _(pd):
    base_url = "https://docs.google.com/spreadsheets/d/"
    doc_id = "1ecopK6oyyb4d_7-QLrCr8YlgFrCetHU7-VQfnYej7JY/"
    format_doc = "export/format=excel"

    url = base_url + doc_id + format_doc

    excel_file = pd.ExcelFile(url)
    return (excel_file,)


@app.cell
def _(excel_file, pd):
    dfs = []

    for sheet in excel_file.sheet_names:
        _df = excel_file.parse(sheet)
        _df["city"] = sheet.split("_")[0]
        _df["type_of_day"] = sheet.split("_")[1]
        dfs.append(_df)

    df = pd.concat(dfs, ignore_index=True)
    return (df,)


@app.cell
def _(mo):
    group_number = 8
    members = ["Sanskriti Vijayvargiya", "Aditi Parab", "Gauri Chitnis"]

    _names = ", ".join(members)

    header_view = mo.Html(f"""
    <div style="background-color: #A37674;
                background-image: none;
                padding: 32px 36px;
                border-radius: 20px;
                color: white;">
      <h1 style="margin: 6px 0 4px 0; font-size: 36px;">What drives Airbnb prices in Europe?</h1>
      <div style="font-size: 17px; opacity: .95;">Group {group_number}</div>
      <div style="margin-top: 14px; font-size: 15px;"><b>Team:</b> {_names}</div>
    </div>
    """)
    return (header_view,)


@app.cell
def _(df, np, pd):

    # Data preparation — cleaning based on our individual drill

    # Create a copy of the original combined dataframe
    listings = df.copy()

    # 1. Remove the first unnamed column
    listings = listings.drop(columns=["Unnamed: 0"], errors="ignore")

    # 2. Combine room_shared and room_private into privacy
    listings["privacy"] = np.where(
        listings["room_shared"],
        "shared",
        np.where(listings["room_type"] == "Private room", "private", None)
    )

    # Remove the original dummy columns
    listings = listings.drop(columns=["room_shared", "room_private"])

    # 3. Convert person_capacity and bedrooms to strings
    listings["person_capacity"] = listings["person_capacity"].astype(str)
    listings["bedrooms"] = listings["bedrooms"].astype(str)

    # 4. Convert Superhost status into readable labels
    listings["host_is_superhost"] = listings["host_is_superhost"].replace({
        True: "superhost",
        False: "normalhost"
    })

    # 5. Create host_listings from multi and biz
    listings["host_listings"] = np.select(
        [
            listings["multi"] == 1,
            listings["biz"] == 1
        ],
        [
            "2-4 listings",
            "More than 4 listings"
        ],
        default="1 listing"
    )

    # Remove the original dummy variables
    listings = listings.drop(columns=["multi", "biz"])

    # 6. Convert total price into nightly price for two people
    listings = listings.rename(columns={"realSum": "price"})
    listings = listings[listings["price"] > 0].copy()
    listings["price"] = listings["price"] / 2

    # Log-transformed nightly price
    listings["log_price"] = np.log(listings["price"])

    # Make city and day labels easier to read
    listings["city"] = listings["city"].str.title()
    listings["type_of_day"] = listings["type_of_day"].str.title()

    # Create a separate readable host category for dashboard charts
    listings["host_type"] = listings["host_is_superhost"].map({
        "superhost": "Superhost",
        "normalhost": "Regular host"
    })

    # ANOVA needs categorical groups.
    # Create distance bands
    listings["distance_band"] = pd.cut(
        listings["dist"],
        bins=[0, 1, 3, 6, np.inf],
        labels=["0-1 km", "1-3 km", "3-6 km", "over 6 km"],
        include_lowest=True
    ).astype("string")

    # Create guest capacity bands using numeric values
    listings["capacity_band"] = pd.cut(
        pd.to_numeric(listings["person_capacity"], errors="coerce"),
        bins=[0, 2, 4, np.inf],
        labels=["1-2 guests", "3-4 guests", "5-6 guests"],
        include_lowest=True
    ).astype("string")

    # Create bedroom bands using numeric values
    listings["bedroom_band"] = pd.cut(
        pd.to_numeric(listings["bedrooms"], errors="coerce"),
        bins=[-1, 0, 1, 2, np.inf],
        labels=["Studio", "1 bedroom", "2 bedrooms", "3+ bedrooms"]
    ).astype("string")

    # Variables available in the dashboard
    factor_options = {
        "City": "city",
        "Room type": "room_type",
        "Distance to centre": "distance_band",
        "Guest capacity": "capacity_band",
        "Bedrooms": "bedroom_band",
        "Weekday vs weekend": "type_of_day",
        "Host type": "host_type",
        "Host listing count": "host_listings"
    }

    # Column name -> dashboard label
    factor_labels = {
        col: name for name, col in factor_options.items()
    }

    # Category ordering for charts
    category_order = {
        "distance_band": ["0-1 km", "1-3 km", "3-6 km", "over 6 km"],
        "capacity_band": ["1-2 guests", "3-4 guests", "5-6 guests"],
        "bedroom_band": ["Studio", "1 bedroom", "2 bedrooms", "3+ bedrooms"],
        "host_listings": ["1 listing", "2-4 listings", "More than 4 listings"]
    }
    return category_order, factor_labels, factor_options, listings


@app.cell
def _(mo):
    # why these variables?
    variables_view = mo.md("""
    ## Variables we chose

    | Variable | Why we chose it |
    |---|---|
    | **City** | Location is probably the biggest factor |
    | **Room type** | Entire home, private vs shared room |
    | **Distance to centre** | Central places have more sights |
    | **Guest capacity** | Bigger places should cost more |
    | **Bedrooms** | Another measure of size |
    | **Weekday vs weekend** | Do prices change at weekends? |
    | **Host type** | Do superhosts charge more? |

    *Price = nightly price for 2 guests.*
    """)
    return (variables_view,)


@app.cell
def _(alt, listings, mo, np, pd):

    # Charts to explore the data

    # Tab 1: Raw price vs log price
    _c1, _e1 = np.histogram(listings["price"], bins=40)
    _raw_df = pd.DataFrame({
        "start": _e1[:-1],
        "end": _e1[1:],
        "count": _c1
    })

    _c2, _e2 = np.histogram(listings["log_price"], bins=40)
    _log_df = pd.DataFrame({
        "start": _e2[:-1],
        "end": _e2[1:],
        "count": _c2
    })

    _raw = alt.Chart(_raw_df).mark_bar(color="#FF5A5F").encode(
        x=alt.X("start:Q", title="Nightly price for 2 guests (€)"),
        x2="end:Q",
        y=alt.Y("count:Q", title="Number of listings"),
    ).properties(
        width=360,
        height=280,
        title="Nightly price: very skewed"
    )

    _log = alt.Chart(_log_df).mark_bar(color="#00A699").encode(
        x=alt.X("start:Q", title="log(price)"),
        x2="end:Q",
        y=alt.Y("count:Q", title="Number of listings"),
    ).properties(
        width=360,
        height=280,
        title="log(price): much more symmetric"
    )

    _tab_skew = alt.hconcat(_raw, _log)


    # Tab 2: Median price per city
    _city = listings.groupby("city")["price"].median().reset_index(
        name="median_price"
    )

    _city_base = alt.Chart(_city).encode(
        y=alt.Y("city:N", sort="-x", title=None),
        x=alt.X("median_price:Q", title="Median nightly price (€)"),
    )

    _city_bars = _city_base.mark_bar(
        cornerRadiusEnd=8,
        size=26
    ).encode(
        color=alt.Color(
            "median_price:Q",
            scale=alt.Scale(scheme="plasma"),
            legend=None
        )
    )

    _city_text = _city_base.mark_text(
        align="left",
        dx=5
    ).encode(
        text=alt.Text("median_price:Q", format=",.0f")
    )

    _tab_city = (_city_bars + _city_text).properties(
        width=650,
        height=360,
        title="Median nightly price by city"
    )


    # Tab 3: Heatmap city x room type
    _heat = listings.groupby(
        ["city", "room_type"]
    )["price"].median().reset_index(name="median_price")

    _middle = _heat["median_price"].median()

    _heat_base = alt.Chart(_heat).encode(
        x=alt.X("room_type:N", title=None),
        y=alt.Y("city:N", title=None),
    )

    _heat_rect = _heat_base.mark_rect().encode(
        color=alt.Color(
            "median_price:Q",
            scale=alt.Scale(scheme="plasma"),
            title="Median €"
        )
    )

    # Text labels inside the heatmap
    _heat_text = _heat_base.mark_text().encode(
        text=alt.Text("median_price:Q", format=",.0f"),
        color=alt.condition(
            alt.datum.median_price > _middle,
            alt.value("black"),
            alt.value("white")
        )
    )

    _tab_heat = (_heat_rect + _heat_text).properties(
        width=450,
        height=380,
        title="Median nightly price: city and room type"
    )


    # Tab 4: Map of the listings
    _sample = listings.sample(
        min(len(listings), 4000),
        random_state=1
    )

    _tab_map = alt.Chart(
        _sample[["lng", "lat", "city", "price"]]
    ).mark_circle(
        size=14,
        opacity=0.6
    ).encode(
        x=alt.X("lng:Q", scale=alt.Scale(zero=False), title="Longitude"),
        y=alt.Y("lat:Q", scale=alt.Scale(zero=False), title="Latitude"),
        color=alt.Color(
            "city:N",
            scale=alt.Scale(scheme="category10"),
            title="City"
        ),
        tooltip=[
            "city",
            alt.Tooltip(
                "price:Q",
                title="Nightly price (€)",
                format=",.0f"
            )
        ],
    ).properties(
        width=700,
        height=400,
        title="Where the listings are (sample of up to 4000)"
    )


    # Display all tabs
    exploration_view = mo.vstack([
        mo.md("## Exploring the data"),
        mo.ui.tabs({
            "Why log?": _tab_skew,
            "Cities": _tab_city,
            "City x room type": _tab_heat,
            "Map": _tab_map,
        }),
    ])
    return (exploration_view,)


@app.cell
def _(factor_options, listings, mo):

    # Controls for boxplots

    x_choice = mo.ui.dropdown(
        options=factor_options,
        value="City",
        label="Compare prices by"
    )

    split_choice = mo.ui.dropdown(
        options={"None": "none", **factor_options},
        value="None",
        label="Split by"
    )

    _all_cities = sorted(listings["city"].unique())

    city_pick = mo.ui.multiselect(
        options=_all_cities,
        value=_all_cities,
        label="Cities"
    )

    log_switch = mo.ui.switch(
        value=True,
        label="Log scale"
    )

    boxplot_controls= mo.vstack([
        mo.md("## Boxplots"),
        mo.hstack([x_choice, split_choice], justify="start"),
        mo.hstack([city_pick, log_switch], justify="start"),
    ])
    return boxplot_controls, city_pick, log_switch, split_choice, x_choice


@app.cell
def _(
    alt,
    category_order,
    city_pick,
    factor_labels,
    listings,
    log_switch,
    mo,
    split_choice,
    x_choice,
):
    # Boxplots

    _x = x_choice.value
    _split = split_choice.value

    _use_split = (_split != "none") and (_split != _x)

    # Filter selected cities
    _data = listings[listings["city"].isin(city_pick.value)].copy()

    mo.stop(
        len(_data) == 0,
        mo.callout(
            mo.md("No city selected. Please choose at least one city."),
            kind="warn"
        )
    )

    # Select grouping columns
    _group_cols = [_x]

    if _use_split:
        _group_cols.append(_split)

    _data = _data[_group_cols + ["price"]].dropna()

    mo.stop(
        len(_data) == 0,
        mo.callout(
            mo.md("No data available for this selection. Please choose different variables."),
            kind="warn"
        )
    )

    # Calculate quartiles for each box
    _q = _data.groupby(
        _group_cols,
        observed=True
    )["price"].quantile(
        [0.25, 0.5, 0.75]
    ).unstack()

    _q.columns = ["q1", "mid", "q3"]
    _q = _q.reset_index()

    # Merge quartiles with original observations
    _m = _data.merge(_q, on=_group_cols)

    # Calculate interquartile range and outlier limits
    _iqr = _m["q3"] - _m["q1"]
    _m["low_limit"] = _m["q1"] - 1.5 * _iqr
    _m["high_limit"] = _m["q3"] + 1.5 * _iqr

    # Calculate whiskers
    _inside = _m[
        (_m["price"] >= _m["low_limit"]) &
        (_m["price"] <= _m["high_limit"])
    ]

    _whiskers = _inside.groupby(
        _group_cols,
        observed=True
    )["price"].agg(
        whisker_low="min",
        whisker_high="max"
    ).reset_index()

    _box_df = _q.merge(_whiskers, on=_group_cols)

    # Identify and sample outliers
    _out = _m[
        (_m["price"] < _m["low_limit"]) |
        (_m["price"] > _m["high_limit"])
    ]

    _out = _out[_group_cols + ["price"]]

    _out = _out.sample(
        min(len(_out), 400),
        random_state=1
    )

    # Select price scale
    if log_switch.value:
        _scale = alt.Scale(type="log")
    else:
        _scale = alt.Scale(type="linear")

    # X-axis
    _x_enc = alt.X(
        f"{_x}:N",
        title=factor_labels[_x],
        sort=category_order.get(_x, "ascending")
    )

    # Colour and positioning
    if _use_split:
        _color = alt.Color(
            f"{_split}:N",
            title=factor_labels[_split],
            scale=alt.Scale(scheme="set2")
        )

        _pos = {"xOffset": alt.XOffset(f"{_split}:N")}
        _width = 14

    else:
        _color = alt.Color(
            f"{_x}:N",
            legend=None,
            scale=alt.Scale(scheme="tableau10")
        )

        _pos = {}
        _width = 40

    # Whisker lines
    _whisker_layer = alt.Chart(_box_df).mark_rule(
        color="#555555"
    ).encode(
        x=_x_enc,
        y=alt.Y(
            "whisker_low:Q",
            scale=_scale,
            title="Nightly price for 2 guests (€)"
        ),
        y2="whisker_high:Q",
        **_pos
    )

    # Box representing the middle 50% of prices
    _box_layer = alt.Chart(_box_df).mark_bar(
        size=_width
    ).encode(
        x=_x_enc,
        y=alt.Y("q1:Q", scale=_scale),
        y2="q3:Q",
        color=_color,
        tooltip=[
            alt.Tooltip("q1:Q", title="25% (Q1)", format=",.2f"),
            alt.Tooltip("mid:Q", title="Median", format=",.2f"),
            alt.Tooltip("q3:Q", title="75% (Q3)", format=",.2f"),
        ],
        **_pos
    )

    # Median line
    _median_layer = alt.Chart(_box_df).mark_tick(
        color="black",
        thickness=2,
        size=_width
    ).encode(
        x=_x_enc,
        y=alt.Y("mid:Q", scale=_scale),
        **_pos
    )

    # Outlier points
    _out_layer = alt.Chart(_out).mark_circle(
        size=15,
        opacity=0.35
    ).encode(
        x=_x_enc,
        y=alt.Y("price:Q", scale=_scale),
        color=_color,
        **_pos
    )

    # Combine all layers
    _boxplot = alt.layer(
        _whisker_layer,
        _out_layer,
        _box_layer,
        _median_layer
    ).properties(
        width=720,
        height=440,
        title="Nightly price by " + factor_labels[_x]
    )

    # Display chart and explanation
    boxplot_view= mo.vstack([
        _boxplot,
        mo.md(
            f"Showing {len(_data):,} listings. "
            "The box represents the middle 50% of prices. "
            "The black line shows the median. "
            "The whiskers show the lowest and highest non-outlier prices. "
            "The dots represent unusually low- or high-priced listings "
            "(only a sample of up to 400 outliers is displayed)."
        )
    ])
    return (boxplot_view,)


@app.cell
def _(alt, factor_options, listings, mo, np, pd, pg):

    # One-way ANOVA for every variable

    _rows = []

    for _name, _col in factor_options.items():

        # Remove rows with missing values in the selected variable
        _data = listings[[_col, "log_price"]].dropna()

        # Check that at least two groups are available
        if _data[_col].nunique() < 2:
            continue

        # Levene test for equality of variances
        _lev = pg.homoscedasticity(
            data=_data,
            dv="log_price",
            group=_col
        )

        # Calculate standard ANOVA for effect size
        _standard = pg.anova(
            data=_data,
            dv="log_price",
            between=_col,
            detailed=True
        )

        _np2 = _standard["np2"].iloc[0]

        if _lev["equal_var"].iloc[0]:

            # Equal variances: use standard one-way ANOVA
            _res = _standard
            _test = "ANOVA"

        else:

            # Unequal variances: use Welch ANOVA
            _res = pg.welch_anova(
                data=_data,
                dv="log_price",
                between=_col
            )
            _test = "Welch ANOVA"

        _rows.append({
            "Variable": _name,
            "Test": _test,
            "F": round(_res["F"].iloc[0], 1),
            "p_unc": _res["p_unc"].iloc[0],
            "np2": round(_np2, 3),
        })


    # Create summary table
    oneway_summary = pd.DataFrame(_rows).sort_values(
        "np2",
        ascending=False
    ).reset_index(drop=True)


    # Classify effect sizes
    oneway_summary["Effect"] = pd.cut(
        oneway_summary["np2"],
        bins=[0, 0.01, 0.06, 0.14, 1.01],
        labels=["negligible", "small", "medium", "large"],
        right=False,
        include_lowest=True
    ).astype(str)


    # Bar chart of effect sizes
    _bars = alt.Chart(oneway_summary).mark_bar(
        cornerRadiusEnd=8,
        size=28
    ).encode(
        y=alt.Y("Variable:N", sort="-x", title=None),
        x=alt.X(
            "np2:Q",
            title="np2 (share of the price variation explained)"
        ),
        color=alt.Color(
            "Effect:N",
            scale=alt.Scale(
                domain=["negligible", "small", "medium", "large"],
                range=["#B8B8B8", "#FFC145", "#FF8A5B", "#FF5A5F"]
            )
        ),
        tooltip=["Variable", "Test", "F", "np2", "Effect"]
    )


    # Dashed lines for effect-size thresholds
    _lines = alt.Chart(
        pd.DataFrame({"x": [0.01, 0.06, 0.14]})
    ).mark_rule(
        strokeDash=[5, 5],
        color="gray"
    ).encode(
        x="x:Q"
    )


    # Format p-values for display
    _show = oneway_summary.copy()

    _show["p_unc"] = np.where(
        _show["p_unc"] < 0.001,
        "< 0.001",
        _show["p_unc"].round(3).astype(str)
    )


    # Display results
    oneway_view = mo.vstack([
        mo.md("""
    ## Analysis of variance

    ### One-way ANOVA for each variable

    The dashed lines mark small (0.01), medium (0.06)
    and large (0.14) effect-size thresholds.

    Welch ANOVA is used when the equal-variance assumption
    is not met. For those variables, np2 is calculated from
    the standard ANOVA as a descriptive effect-size estimate.
    """),

        (_bars + _lines).properties(
            width=620,
            height=320,
            title="Which variable explains the most price variation?"
        ),

        mo.ui.table(_show, selection=None)
    ])
    return (oneway_view,)


@app.cell
def _(factor_options, mo):
    # controls for one-way ANOVA table
    oneway_pick = mo.ui.dropdown(options=factor_options, value="City", label="Show details for")
    oneway_controls = mo.vstack([mo.md("### One-way ANOVA in detail"), oneway_pick])
    return oneway_controls, oneway_pick


@app.cell
def _(factor_labels, listings, mo, np, oneway_pick, pg):
    _col = oneway_pick.value
    _name = factor_labels[_col]

    # Remove missing observations
    _data = listings[[_col, "log_price", "price"]].dropna()

    # Check that at least two groups exist
    if _data[_col].nunique() < 2:
        mo.stop(
            True,
            mo.callout(
                mo.md(f"Not enough groups available for {_name}."),
                kind="warn"
            )
        )

    # Check equality of variances
    _lev = pg.homoscedasticity(
        data=_data,
        dv="log_price",
        group=_col
    )

    _equal_var = _lev["equal_var"].iloc[0]

    # Standard ANOVA, used to calculate descriptive np2
    _standard = pg.anova(
        data=_data,
        dv="log_price",
        between=_col,
        detailed=True
    )

    _np2 = _standard["np2"].iloc[0]

    # Select appropriate statistical test
    if _equal_var:
        _result = _standard
        _test_name = "Standard one-way ANOVA"
    else:
        _result = pg.welch_anova(
            data=_data,
            dv="log_price",
            between=_col
        )
        _test_name = "Welch's one-way ANOVA"

    _p = _result["p_unc"].iloc[0]
    _f = _result["F"].iloc[0]

    # Compare group prices
    _groups = (
        _data.groupby(_col, observed=True)
        .agg(
            mean_log_price=("log_price", "mean"),
            median_price=("price", "median"),
            count=("price", "size")
        )
        .reset_index()
    )

    # Convert mean log price back to euros
    _groups["typical_price"] = np.exp(
        _groups["mean_log_price"]
    )

    _highest = _groups.loc[_groups["typical_price"].idxmax()]
    _lowest = _groups.loc[_groups["typical_price"].idxmin()]

    _high_name = str(_highest[_col])
    _low_name = str(_lowest[_col])

    _high_price = _highest["typical_price"]
    _low_price = _lowest["typical_price"]

    # Effect size interpretation
    if _np2 < 0.01:
        _effect = "negligible"
    elif _np2 < 0.06:
        _effect = "small"
    elif _np2 < 0.14:
        _effect = "medium"
    else:
        _effect = "large"

    # Dynamic hypothesis and conclusion
    if _p < 0.05:
        _conclusion = (
            f"We reject the null hypothesis. There is evidence "
            f"that mean log prices differ across {_name.lower()} groups."
        )
    else:
        _conclusion = (
            f"We do not reject the null hypothesis. We do not have "
            f"enough evidence of different mean log prices across "
            f"{_name.lower()} groups."
        )

    _interpretation = mo.md(f"""
    ### Hypothesis and interpretation: {_name}

    **Null hypothesis (H₀):** The mean log-transformed nightly
    Airbnb price is equal across all groups of {_name.lower()}.

    **Alternative hypothesis (H₁):** At least one group has a
    different mean log-transformed nightly Airbnb price.

    **Test used:** {_test_name}

    **Test result:** F = {_f:.2f}, p-value =
    {"< 0.001" if _p < 0.001 else f"{_p:.3f}"}.

    **Effect size:** np2 = {_np2:.3f} ({_effect} effect).
    This means the factor explains approximately {_np2 * 100:.1f}%
    of the variation relative to the factor plus residual variation.

    **Price comparison:** {_high_name} has the highest typical
    price (approximately €{_high_price:.2f}), while {_low_name}
    has the lowest (approximately €{_low_price:.2f}).

    **Conclusion:** {_conclusion}

    *The price comparison uses the geometric mean of log prices.
    The np2 value for Welch's test is taken from standard ANOVA
    as a descriptive effect-size estimate.*
    """)

    oneway_detail_view = mo.vstack([
        mo.md(f"### Detailed results for {_name}"),
        mo.ui.table(
            _result.round({"SS": 1, "MS": 3, "F": 2, "np2": 3}),
            selection=None
        ),
        _interpretation
    ])
    return (oneway_detail_view,)


@app.cell
def _(mo):
    # controls for two-way ANOVA
    twoway_controls = mo.md("## Two-way ANOVA: City × Room type")
    return


@app.cell
def _(alt, category_order, listings, mo, np, pg):

    _a = "city"
    _b = "room_type"
    _name_a = "City"
    _name_b = "Room type"

    _two_data = listings[[_a, _b, "log_price", "price"]].dropna().copy()

    mo.stop(
        len(_two_data) == 0 or _two_data[_a].nunique() < 2 or _two_data[_b].nunique() < 2,
        mo.callout(
            mo.md("There is not enough data to run the City × Room type two-way ANOVA."),
            kind="warn"
        )
    )

    # Run the two-way ANOVA with the interaction term.
    _table = pg.anova(
        data=_two_data,
        dv="log_price",
        between=[_a, _b],
        detailed=True
    )

    # Give the rows clear, reader-friendly names.
    _table = _table.copy()
    if len(_table) >= 4:
        _table.loc[_table.index[0], "Source"] = "City"
        _table.loc[_table.index[1], "Source"] = "Room type"
        _table.loc[_table.index[2], "Source"] = "City × Room type"
        _table.loc[_table.index[3], "Source"] = "Residual"

    # Mean log price for each city/room-type combination, converted to euros.
    _means = (
        _two_data.groupby([_a, _b], observed=True)["log_price"]
        .mean()
        .reset_index()
    )
    _means["typical_price"] = np.exp(_means["log_price"])

    _line_chart = alt.Chart(_means).mark_line(
        point=alt.OverlayMarkDef(size=90),
        strokeWidth=3
    ).encode(
        x=alt.X(
            "city:N",
            title="City",
            sort=category_order.get("city", "ascending")
        ),
        y=alt.Y(
            "typical_price:Q",
            title="Typical nightly price (€; log scale)",
            scale=alt.Scale(type="log")
        ),
        color=alt.Color(
            "room_type:N",
            title="Room type",
            scale=alt.Scale(scheme="set1")
        ),
        tooltip=[
            alt.Tooltip("city:N", title="City"),
            alt.Tooltip("room_type:N", title="Room type"),
            alt.Tooltip("typical_price:Q", title="Typical price (€)", format=",.2f")
        ],
    ).properties(
        width=700,
        height=380,
        title="Interaction plot: City × Room type"
    )

    twoway_summary = _table.iloc[:3].copy().reset_index(drop=True)
    twoway_summary["Factor"] = ["City", "Room type", "City × Room type"]

    twoway_view = mo.vstack([
        mo.md("### Two-way ANOVA results"),
        mo.ui.table(
            _table.round({"SS": 1, "MS": 3, "F": 2, "np2": 3}),
            selection=None
        ),
        mo.md(
            "The interaction plot compares typical nightly prices across cities "
            "for each room type. Roughly parallel lines suggest a weaker interaction; "
            "different slopes or crossing lines suggest that the room-type price "
            "difference varies by city. Use the interaction p-value in the ANOVA table "
            "to assess statistical evidence for this pattern."
        ),
        _line_chart,
    ], gap=2)
    return (twoway_view,)


@app.cell
def _(mo):
    twoway_hypothesis_view = mo.md("""
    ### Hypotheses: City × Room type

    **1. Main effect of City**
    - H₀: Mean log-transformed nightly prices are equal across all cities.
    - H₁: At least one city has a different mean log-transformed nightly price.

    **2. Main effect of Room type**
    - H₀: Mean log-transformed nightly prices are equal across all room types.
    - H₁: At least one room type has a different mean log-transformed nightly price.

    **3. Interaction: City × Room type**
    - H₀: There is no interaction between city and room type; the effect of room type on price is the same across cities.
    - H₁: There is an interaction; the effect of room type on price depends on the city.

    A p-value below 0.05 provides evidence against the corresponding null hypothesis.
    """)
    return (twoway_hypothesis_view,)


@app.cell
def _(factor_options, listings, mo, pd, pg):

    # One-way ANOVA: checking assumptions

    from scipy.stats import shapiro

    _assumption_rows = []

    for _name, _col in factor_options.items():

        # Remove missing observations
        _data = listings[[_col, "log_price"]].dropna()

        # Count observations in each group
        _group_sizes = _data.groupby(
            _col,
            observed=True
        ).size()

        if len(_group_sizes) < 2:
            continue

        # 1. Equal variances: Levene's test
        _lev = pg.homoscedasticity(
            data=_data,
            dv="log_price",
            group=_col
        )

        _levene_p = _lev["pval"].iloc[0]

        # 2. Normality: calculate residuals
        _group_means = _data.groupby(
            _col,
            observed=True
        )["log_price"].transform("mean")

        _residuals = _data["log_price"] - _group_means

        # Use a sample for the Shapiro-Wilk test
        _sample = _residuals.sample(
            min(len(_residuals), 5000),
            random_state=42
        )

        _shapiro = shapiro(_sample)
        _shapiro_p = _shapiro.pvalue

        # Save the results
        _assumption_rows.append({
            "Variable": _name,
            "Number of groups": len(_group_sizes),
            "Smallest group": _group_sizes.min(),
            "Largest group": _group_sizes.max(),
            "Levene p-value": _levene_p,
            "Equal variances": (
                "Yes" if _levene_p >= 0.05 else "No"
            ),
            "Shapiro p-value": _shapiro_p,
            "Normality supported": (
                "Yes" if _shapiro_p >= 0.05 else "No"
            )
        })


    # Create the assumption summary
    assumption_summary = pd.DataFrame(_assumption_rows)

    # Format p-values
    _assumption_display = assumption_summary.copy()

    for _column in ["Levene p-value", "Shapiro p-value"]:
        _assumption_display[_column] = (
            _assumption_display[_column].apply(
                lambda p: "< 0.001" if p < 0.001 else round(p, 3)
            )
        )


    # Display the results
    assumptions_view = mo.vstack([
        mo.md("""
    ## Checking the ANOVA assumptions

    Before comparing Airbnb prices, we check whether our data
    are suitable for ANOVA.

    - **Equal variances:** Are price variations similar across groups?
    - **Normality:** Are the differences between individual prices
      and their group averages approximately normally distributed?
    - **Group sizes:** Do we have enough listings in each group?

    A p-value below 0.05 indicates evidence against the
    corresponding assumption.
    """),

        mo.ui.table(
            _assumption_display,
            selection=None
        ),

        mo.md("""
    **Independence:** We assume that listings are independent.
    However, this cannot be confirmed using these statistical tests.
    For example, multiple listings from the same host may be related.


    """)
    ])
    return assumptions_view, shapiro


@app.cell
def _(mo):
    assumption_interpretation_view = mo.md("""
    ## What do these results tell us?

    Most variables show unequal variances, so we use **Welch's ANOVA**
    for these comparisons. For weekdays vs weekends, equal variances
    are supported, so we use standard ANOVA.

    The Shapiro-Wilk test indicates deviations from normality.
    However, with such a large dataset, even small deviations can
    result in significant p-values.

    We also assume that listings are independent, although this
    may not always be the case if one host manages multiple properties.

    Overall, we consider these limitations when interpreting our results.
    """)
    return (assumption_interpretation_view,)


@app.cell
def _(listings, mo, pd, pg, shapiro):

    # Two-way ANOVA: City × Room type assumptions

    # from scipy.stats import shapiro
    import statsmodels.formula.api as smf

    # Prepare data
    _two_data = listings[
        ["city", "room_type", "log_price"]
    ].dropna().copy()

    # Create city and room type combinations
    _two_data["_combination"] = (
        _two_data["city"].astype(str) + " × " +
        _two_data["room_type"].astype(str)
    )

    # Group sizes
    _group_sizes = _two_data.groupby(
        "_combination",
        observed=True
    ).size()

    # 1. Equal variances: Levene's test
    _lev = pg.homoscedasticity(
        data=_two_data,
        dv="log_price",
        group="_combination"
    )

    _levene_p = _lev["pval"].iloc[0]

    # 2. Fit two-way ANOVA model
    _model = smf.ols(
        'log_price ~ C(city) * C(room_type)',
        data=_two_data
    ).fit()

    # Calculate residuals
    _residuals = _model.resid

    # Shapiro-Wilk test on a sample
    _sample = _residuals.sample(
        min(len(_residuals), 5000),
        random_state=42
    )

    _shapiro_p = shapiro(_sample).pvalue

    # Results table
    _two_assumptions = pd.DataFrame([{
        "Factors": "City × Room type",
        "Combinations": len(_group_sizes),
        "Smallest group": _group_sizes.min(),
        "Largest group": _group_sizes.max(),
        "Levene p-value": _levene_p,
        "Equal variances": "Yes" if _levene_p >= 0.05 else "No",
        "Shapiro p-value": _shapiro_p,
        "Normality supported": "Yes" if _shapiro_p >= 0.05 else "No"
    }])

    # Format p-values
    _two_display = _two_assumptions.copy()

    for _column in ["Levene p-value", "Shapiro p-value"]:
        _two_display[_column] = _two_display[_column].apply(
            lambda p: "< 0.001" if p < 0.001 else round(p, 3)
        )

    twoway_assumptions_view = mo.vstack([
        mo.md("""
    ### Assumption checks: City × Room type

    We check equal variances across City × Room type combinations
    using Levene's test and check residual normality using
    the Shapiro-Wilk test.

    We also report the number of listings in each combination.
    Independence is assumed but cannot be directly tested here.
    """),
        mo.ui.table(_two_display, selection=None)
    ])
    return (twoway_assumptions_view,)


@app.cell
def _(mo):
    twoway_interpretation_view = mo.md("""
    ## What do the two-way ANOVA results tell us?

    The two-way ANOVA examines whether Airbnb prices differ across
    cities and room types, and whether the effect of room type
    changes depending on the city.

    - **City:** City has a large effect on Airbnb prices
      (np2 = 0.450). This indicates that location is an important
      factor associated with differences in nightly prices.

    - **Room type:** Room type also has a large effect
      (np2 = 0.315). This means that the type of accommodation
      offered is strongly associated with its price.

    - **City × Room type interaction:** The interaction has a
      small effect (np2 = 0.049). This indicates that the price
      differences between room types vary across cities.

    All three effects are statistically significant (p < 0.001).

    **Overall conclusion:**

    Both location and room type play an important role in Airbnb
    pricing. Additionally, the relationship between room type
    and price is not exactly the same in every city.

    This suggests that Airbnb prices depend not only on where
    a property is located and what type of accommodation it offers,
    but also on how these two factors work together.
    """)
    return (twoway_interpretation_view,)


@app.cell
def _(
    assumption_interpretation_view,
    assumptions_view,
    boxplot_controls,
    boxplot_view,
    exploration_view,
    header_view,
    mo,
    oneway_controls,
    oneway_detail_view,
    oneway_view,
    twoway_assumptions_view,
    twoway_hypothesis_view,
    twoway_interpretation_view,
    twoway_view,
    variables_view,
):
    # One-way ANOVA tab
    one_way_tab = mo.vstack([
        oneway_view,
        mo.hstack(
            [oneway_controls, oneway_detail_view],
            align="start",
            gap=2,
        ),
        assumptions_view,
        assumption_interpretation_view,
    ], gap=2)


    # Two-way ANOVA tab
    two_way_tab = mo.vstack([
        twoway_assumptions_view,
        twoway_view,
        twoway_hypothesis_view,
        twoway_interpretation_view,
    ], gap=2)


    anova_tabs = mo.ui.tabs({
        "One-way ANOVA": one_way_tab,
        "Two-way ANOVA": two_way_tab,
    })


    dashboard = mo.vstack([
        header_view,
        variables_view,
        exploration_view,
        mo.hstack(
            [boxplot_controls, boxplot_view],
            align="start",
            gap=2,
        ),
        mo.md("## Statistical analysis"),
        anova_tabs,
    ], gap=2)
    return (dashboard,)


@app.cell
def _(dashboard):
    dashboard
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
