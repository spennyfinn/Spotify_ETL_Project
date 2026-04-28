# Statistics & Hypothesis Testing Practice
## Using Your Music Streaming Dataset

This guide outlines statistical analyses you can run on your own data.
Every test listed here maps to real columns in your database exports.

---

## Data You Have Available

| File | Key Columns |
|------|-------------|
| `songs.csv` | popularity, is_explicit, engagement_ratio, song_listeners, duration_ms, release_date, track_number |
| `artists.csv` | artist_popularity, artist_followers, total_listeners, total_playcount, plays_per_listener, on_tour |
| `albums.csv` | album_type (single/compilation/album), album_total_tracks |
| `song_audio_features.csv` | bpm, energy, danceability, spectral_centroid, zero_crossing_rate, harmonic_ratio, percussive_ratio |

---

## SECTION 1: Descriptive Statistics
### What it is:
Summarizing and understanding your data before running any tests.
This is always your first step.

### What to do:
- Compute mean, median, std, min, max for `popularity`, `energy`, `bpm`, `danceability`
- Plot histograms for each numeric column
- Check for skew - is `popularity` normally distributed or skewed?
- Identify outliers using boxplots

### Key concept:
**Normal distribution** - many statistical tests assume your data is roughly bell-shaped.
If it is not, you may need non-parametric alternatives (covered later).

### Questions to answer:
- What does the average song popularity look like?
- Is BPM normally distributed?
- Are there outlier songs with extremely high engagement ratios?

---

## SECTION 2: Correlation Analysis
### What it is:
Measuring the strength and direction of the relationship between two numeric variables.
Correlation ranges from -1 (perfect negative) to +1 (perfect positive). 0 means no relationship.

### What to do:
- Compute a correlation matrix across all numeric features
- Plot a heatmap of correlations
- Scatter plots for strong correlations (r > 0.3 or r < -0.3)

### Key concept:
**Pearson correlation** - measures linear relationships between two continuous variables.
**Correlation ≠ causation** - two things can move together without one causing the other.

### Specific questions to test:
- Does `artist_popularity` correlate with `song popularity`?
- Does `energy` correlate with `danceability`?
- Does `artist_followers` correlate with `total_playcount`?
- Does `bpm` correlate with `engagement_ratio`?

---

## SECTION 3: Two-Sample T-Test
### What it is:
Tests whether two groups have significantly different means.
For example: "Do explicit songs have higher popularity than clean songs ON AVERAGE,
or is that difference just random chance?"

### When to use it:
- Comparing two groups (yes/no, group A vs group B)
- Your outcome variable is continuous (popularity, energy, etc.)
- Your data is roughly normally distributed (or n > 30)

### Key concepts:
- **Null hypothesis (H0):** There is no difference between the two groups
- **Alternative hypothesis (H1):** There IS a difference
- **p-value:** Probability of seeing this result if H0 were true. If p < 0.05, reject H0
- **Alpha (α):** Your threshold for significance. Standard is 0.05 (5%)

### Tests to run with your data:

#### Test 1: Explicit vs Clean Songs
```
H0: Explicit songs have the same average popularity as clean songs
H1: Explicit songs have different average popularity than clean songs
Groups: songs where is_explicit = True vs is_explicit = False
Outcome: popularity
```

#### Test 2: On Tour vs Off Tour Artists
```
H0: Artists on tour have the same average followers as artists not on tour
H1: Artists on tour have more followers than artists not on tour
Groups: artists where on_tour = True vs on_tour = False
Outcome: artist_followers
```

#### Test 3: Singles vs Albums
```
H0: Songs from singles have the same average popularity as songs from albums
H1: Songs from singles have higher popularity than songs from albums
Groups: album_type = 'single' vs album_type = 'album'
Outcome: song popularity
```

#### Test 4: High Energy vs Low Energy Songs
```
H0: High energy songs (energy > 0.6) have the same popularity as low energy songs
H1: High energy songs have different popularity than low energy songs
Groups: energy > 0.6 vs energy <= 0.6 (you define the threshold)
Outcome: popularity
```

---

## SECTION 4: One-Way ANOVA
### What it is:
Like a t-test but for 3+ groups at once.
Tests whether at least one group mean is significantly different from the others.

### When to use it:
- Comparing 3 or more groups simultaneously
- Running multiple t-tests inflates your false positive rate - ANOVA avoids this

### Key concepts:
- **F-statistic:** Ratio of variance between groups to variance within groups
- **Post-hoc test:** If ANOVA is significant, run Tukey HSD to find WHICH groups differ
- **p < 0.05:** At least one group is significantly different

### Tests to run with your data:

#### Test 1: Popularity by Album Type
```
H0: Average popularity is the same across singles, albums, and compilations
H1: At least one album type has different average popularity
Groups: album_type = 'single', 'album', 'compilation'
Outcome: popularity
Follow up: Tukey HSD to see which pairs differ
```

#### Test 2: Popularity by Decade
```
H0: Average popularity is the same across decades
H1: Songs from some decades are significantly more popular
Groups: 1980s, 1990s, 2000s, 2010s, 2020s (derived from release_date)
Outcome: popularity
```

#### Test 3: BPM by Decade
```
H0: Average BPM has not changed across decades
H1: Average BPM differs significantly across decades
Groups: same decade bins as above
Outcome: bpm
```

---

## SECTION 5: Chi-Square Test
### What it is:
Tests whether two categorical variables are independent of each other.
For example: "Is being explicit related to being playable, or are they independent?"

### When to use it:
- Both variables are categorical (yes/no, type A/B/C)
- You have counts of observations in each category combination

### Key concepts:
- **Contingency table:** A table showing counts for each combination of categories
- **Expected frequencies:** What counts you would expect if variables were independent
- **p < 0.05:** The two variables are NOT independent (they are associated)

### Tests to run with your data:

#### Test 1: Explicit vs Playable
```
H0: Whether a song is explicit is independent of whether it is playable
H1: Explicit songs are more/less likely to be playable
Variables: is_explicit, is_playable
```

#### Test 2: On Tour vs Has Genres
```
H0: Whether an artist is on tour is independent of whether they have genre tags
H1: Artists on tour are more likely to have genre tags
Variables: on_tour, has_genres
```

---

## SECTION 6: Non-Parametric Tests
### What it is:
Tests that do NOT assume your data is normally distributed.
Use these when your data is skewed, has outliers, or has small sample sizes.

### When to use them:
- Your data fails a normality test (Shapiro-Wilk)
- You have ordinal data (rankings, not continuous measurements)
- Small sample sizes (n < 30)

### Key tests:

#### Mann-Whitney U Test
The non-parametric equivalent of a t-test.
Compares the distributions of two groups without assuming normality.

```
Same questions as your t-tests above, but use this when:
- popularity distribution is heavily skewed
- you have significant outliers
```

#### Kruskal-Wallis Test
The non-parametric equivalent of ANOVA.
Use instead of ANOVA when your groups are not normally distributed.

```
Same questions as your ANOVA tests above, but use this when:
- popularity is not normally distributed across groups
```

#### Spearman Correlation
The non-parametric equivalent of Pearson correlation.
Use when your relationship is monotonic but not linear,
or when data is not normally distributed.

```
Same correlation questions from Section 2, but use this for:
- skewed variables like artist_followers or total_playcount
```

---

## SECTION 7: Effect Size
### What it is:
Statistical significance (p-value) tells you IF an effect exists.
Effect size tells you HOW BIG that effect is.
A result can be statistically significant but practically meaningless.

### Why it matters:
With 333K songs, almost everything will be statistically significant
because large samples detect even tiny differences.
Effect size tells you if the difference actually matters.

### Key measures:

#### Cohen's d (for t-tests)
- d < 0.2: Negligible effect
- d = 0.2: Small effect
- d = 0.5: Medium effect
- d = 0.8: Large effect

#### Eta-squared η² (for ANOVA)
- η² < 0.01: Small effect
- η² = 0.06: Medium effect
- η² = 0.14: Large effect

### What to do:
After every t-test and ANOVA you run, also compute the effect size.
Report both: "Explicit songs had significantly higher popularity (p < 0.001, d = 0.23)"

---

## SECTION 8: Confidence Intervals
### What it is:
A range of values that likely contains the true population parameter.
A 95% confidence interval means: if you repeated this study 100 times,
95 of those intervals would contain the true mean.

### What to do:
- Compute 95% CI for mean popularity of explicit vs clean songs
- Compute 95% CI for mean energy of songs by decade
- Plot CIs on bar charts to visually show uncertainty

### Key concept:
If two confidence intervals do not overlap, the groups are likely significantly different.
If they overlap, the difference may not be significant.

---

## SECTION 9: Full Analysis Workflow (Putting It All Together)

### Example: "Do explicit songs have higher popularity?"

```
Step 1: Descriptive stats
  - Compute mean popularity for explicit vs clean songs
  - Plot side-by-side histograms

Step 2: Check normality
  - Run Shapiro-Wilk test on each group
  - If p > 0.05: data is normal, use t-test
  - If p < 0.05: data is not normal, use Mann-Whitney U

Step 3: Run the test
  - T-test (or Mann-Whitney) with alpha = 0.05
  - Report: t-statistic, p-value, degrees of freedom

Step 4: Compute effect size
  - Cohen's d for t-test
  - Report: small/medium/large

Step 5: Compute confidence intervals
  - 95% CI for mean popularity in each group

Step 6: Write conclusion
  - "Explicit songs (M=XX, SD=XX) had significantly higher popularity than clean songs
     (M=XX, SD=XX), t(df)=XX, p=XX, d=XX (small/medium/large effect).
     The 95% CI for the difference was [XX, XX]."
```

---

## SECTION 10: Suggested Analysis Order for a Beginner

Start here and work through in order:

1. **Load your data** - read CSVs, join tables, check shapes and dtypes
2. **Descriptive stats** - .describe(), histograms, value_counts()
3. **Correlation heatmap** - understand relationships before testing
4. **One t-test** - explicit vs clean songs on popularity (simplest case)
5. **Add normality check** - Shapiro-Wilk, decide t-test vs Mann-Whitney
6. **Add effect size** - Cohen's d for your t-test
7. **Add confidence intervals** - visualize uncertainty
8. **Run ANOVA** - popularity by album type (3 groups)
9. **Add Tukey HSD** - which album types actually differ
10. **Run chi-square** - explicit vs playable (categorical test)
11. **Write up conclusions** - practice explaining results in plain English

---

## Libraries You Will Need

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats
from scipy.stats import (
    ttest_ind,          # two-sample t-test
    mannwhitneyu,       # non-parametric t-test alternative
    f_oneway,           # one-way ANOVA
    kruskal,            # non-parametric ANOVA alternative
    chi2_contingency,   # chi-square test
    shapiro,            # normality test
    pearsonr,           # pearson correlation
    spearmanr           # spearman correlation
)

from statsmodels.stats.multicomp import pairwise_tukeyhsd   # post-hoc ANOVA
import statsmodels.stats.api as sms                          # confidence intervals
```

---

## Useful Terms Cheat Sheet

| Term | Plain English |
|------|--------------|
| p-value | Probability this result happened by chance. Lower = more significant |
| α (alpha) | Your significance threshold. Usually 0.05 |
| H0 | Null hypothesis - assuming no effect or difference |
| H1 | Alternative hypothesis - what you think is actually true |
| Reject H0 | p < α, your result is statistically significant |
| Fail to reject H0 | p > α, not enough evidence to conclude a difference |
| Effect size | How big the difference actually is (not just whether it exists) |
| Statistical power | Probability of detecting a real effect if one exists |
| Type I error | False positive - you rejected H0 but it was actually true |
| Type II error | False negative - you failed to reject H0 but it was actually false |
| Normal distribution | Bell curve - many tests assume your data looks like this |
| Parametric test | Assumes a specific data distribution (usually normal) |
| Non-parametric test | Makes no distribution assumptions - more flexible |
| Confidence interval | Range that likely contains the true population value |
| Degrees of freedom | Roughly: sample size minus number of groups |

---

## Suggested Questions to Investigate (In Plain English)

These are real business questions you can answer with your data:

1. Are explicit songs more popular than clean songs?
2. Do artists on tour have more followers?
3. Which album format (single, album, compilation) produces the most popular songs?
4. Has average song popularity changed across decades?
5. Has BPM (tempo) changed across decades?
6. Do more energetic songs get higher engagement?
7. Is there a relationship between danceability and popularity?
8. Do songs with higher harmonic ratios (more melodic) have higher popularity?
9. Is being explicit related to whether a song is playable on Spotify?
10. Do artists with more followers have higher plays per listener?

---

## Good Luck!

The goal is not to memorize formulas.
The goal is to understand:
- WHAT question am I asking?
- WHICH test answers that question?
- HOW do I interpret the result?
- HOW BIG is the effect?
- HOW do I communicate this to someone non-technical?

Start with Section 1 and Section 3 (t-test).
Once those feel comfortable, work your way through the rest.
