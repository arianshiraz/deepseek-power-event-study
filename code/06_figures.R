# Figures for the DeepSeek / stacked-event study (tidyplots + ggdist).
# Run from the repository root after the Python stages: Rscript code/06_figures.R
# Each figure is written as PDF (paper) and PNG (README).

suppressPackageStartupMessages({
  library(readr); library(dplyr); library(tidyr)
  library(ggplot2); library(tidyplots); library(ggdist); library(distributional)
})

tab <- function(f) read_csv(file.path("output", "tables", f), show_col_types = FALSE)
fig <- file.path("output", "figures")
dir.create(fig, showWarnings = FALSE, recursive = TRUE)

group_levels <- c("merchant", "hybrid", "regulated", "placebo")
group_labels <- c(merchant = "Merchant", hybrid = "Hybrid", regulated = "Regulated",
                  placebo = "Water & gas, placebo")
short_labels <- c(pjm_bra = "PJM capacity auction, Jul 2024 (+)",
                  crane_ppa = "Crane PPA, Sep 2024 (+); CEG excluded",
                  ferc_isa = "FERC rejects Talen ISA, Nov 2024 (-); TLN excluded",
                  deepseek = "DeepSeek, Jan 2025 (-)")
okabe <- as.vector(unclass(colors_discrete_okabeito))  # plain hex strings
names(okabe) <- NULL
group_cols <- setNames(okabe[c(6, 1, 3, 2)], group_labels)  # vermillion, orange, green, sky
sign_cols <- c("Positive AI-load news" = okabe[3], "Negative AI-load news" = okabe[6],
               "Pooled, sign-adjusted" = "#000000")

save_both <- function(p, name, width, height) {
  for (ext in c("pdf", "png")) {
    ggsave(file.path(fig, paste0(name, ".", ext)), p, width = width, height = height,
           units = "mm", dpi = 300, bg = "white")
  }
}

# Figure 1. DeepSeek: mean cumulative abnormal return by group, 95% CI across firms.
paths <- tab("deepseek_ar_paths.csv") |>
  mutate(group = factor(group_labels[group], levels = group_labels),
         car_pct = 100 * car)
n_by <- paths |> distinct(ticker, group) |> count(group)
paths <- paths |>
  left_join(n_by, by = "group") |>
  mutate(group_n = factor(paste0(group, " (n=", n, ")"),
                          levels = paste0(n_by$group, " (n=", n_by$n, ")")))

p1 <- paths |>
  tidyplot(x = rel, y = car_pct, color = group_n) |>
  add_ci95_ribbon(alpha = 0.15) |>
  add_mean_line(linewidth = 0.6) |>
  add_reference_lines(x = -0.5, y = 0) |>
  adjust_colors(unname(group_cols[as.character(n_by$group)])) |>
  adjust_x_axis_title("Trading days relative to 27 January 2025") |>
  adjust_y_axis_title("Cumulative abnormal return (%)") |>
  adjust_legend_title("") |>
  adjust_font(fontsize = 8) |>
  adjust_size(width = 110, height = 60, unit = "mm")
save_both(p1, "fig1_deepseek_car_paths", 170, 80)

# Figure 2. Exposure slope by event (confidence distributions) and the pooled estimate.
sl <- tab("stacked_event_slopes.csv") |>
  transmute(label, est = 100 * beta_e, se = 100 * se_HC3,
            kind = ifelse(sign > 0, "Positive AI-load news", "Negative AI-load news"),
            date = as.Date(date))
pooled <- tab("stacked_pooled.csv") |> filter(startsWith(spec, "main")) |>
  transmute(label = "Pooled (sign-adjusted)", est = 100 * beta, se = 100 * se_firm_cluster,
            kind = "Pooled, sign-adjusted", date = as.Date("2099-01-01"))
sl2 <- bind_rows(sl, pooled) |> arrange(desc(date)) |>
  mutate(label = factor(label, levels = label),
         kind = factor(kind, levels = names(sign_cols)))

p2 <- ggplot(sl2, aes(y = label, xdist = dist_normal(est, se), color = kind, fill = kind)) +
  geom_vline(xintercept = 0, linetype = 2, linewidth = 0.3) +
  stat_halfeye(.width = c(0.5, 0.95), slab_alpha = 0.25, point_size = 1.6,
               normalize = "groups") +
  scale_color_manual(values = sign_cols, name = NULL) +
  scale_fill_manual(values = sign_cols, name = NULL) +
  labs(x = "Effect on CAR[0,1] of +100 MW per $bn uncontracted merchant capacity (pp)",
       y = NULL) +
  theme_classic(base_size = 8) +
  theme(legend.position = "bottom")
save_both(p2, "fig2_event_slopes", 150, 85)

# Figure 3. Firm CAR[0,1] against exposure, one panel per event (parties excluded).
fe <- tab("stacked_firm_event.csv") |>
  filter(!excluded_party) |>
  mutate(group = factor(group_labels[group], levels = group_labels),
         x_mw = 100 * x, car_pct = 100 * CAR01,
         event_lab = factor(short_labels[event], levels = short_labels))

p3 <- fe |>
  tidyplot(x = x_mw, y = car_pct, color = group) |>
  add_reference_lines(y = 0) |>
  add_data_points(size = 1.4, alpha = 0.8, white_border = TRUE) |>
  adjust_colors(unname(group_cols)) |>
  adjust_x_axis_title("Uncontracted merchant MW per $bn of equity (pre-event)") |>
  adjust_y_axis_title("CAR[0,1] (%)") |>
  remove_legend_title() |>
  adjust_font(fontsize = 8) |>
  adjust_size(width = NA, height = NA)
p3 <- p3 +
  geom_smooth(aes(group = 1), method = "lm", formula = y ~ x, se = TRUE,
              color = "grey30", fill = "grey80", linewidth = 0.4) +
  facet_wrap(~event_lab, ncol = 2) +
  labs(color = NULL) +
  theme(strip.background = element_blank(), strip.text = element_text(hjust = 0),
        legend.position = "bottom")
save_both(p3, "fig3_event_scatter", 170, 130)

# Figure 4. Placebo-date distribution of the pooled slope against the actual estimate.
draws <- tab("stacked_placebo_draws.csv") |> mutate(beta_pp = 100 * beta)
actual <- 100 * pooled$est / 100
p_one <- tab("stacked_pooled.csv") |> filter(startsWith(spec, "main")) |>
  pull(p_placebo_one_sided)

p4 <- ggplot(draws, aes(x = beta_pp)) +
  stat_dots(quantiles = 100, fill = okabe[2], color = NA) +
  geom_vline(xintercept = actual, color = okabe[6], linewidth = 0.7) +
  annotate("text", x = actual, y = 0.95, hjust = 1.05, size = 2.8,
           label = sprintf("Actual: %.2f pp\n(%d of %d placebo draws as large)",
                           actual, round(p_one * nrow(draws)), nrow(draws))) +
  labs(x = "Pooled sign-adjusted slope on 4 random non-event dates (pp per 100 MW/$bn)",
       y = NULL) +
  theme_classic(base_size = 8) +
  theme(axis.text.y = element_blank(), axis.ticks.y = element_blank(),
        axis.line.y = element_blank())
save_both(p4, "fig4_placebo_dates", 150, 70)

# Figure 5. Pooled exposure slope under the AI-beta control specifications (section 8d).
spec_labels <- c(
  "market model, no control (reference)" = "Reference: market model",
  "two-factor abnormal returns (primary)" = "Two-factor returns (primary)",
  "market model + event-specific AI-beta control" = "Free event-specific AI-beta control",
  "exploratory: market model + AI beta x factor move" = "AI beta x AI move (exploratory)")
ab <- tab("ai_beta_pooled.csv") |>
  mutate(spec = factor(spec_labels[spec], levels = rev(spec_labels)),
         factor = factor(factor, levels = c("SMH", "NVDA")),
         est = 100 * beta, se = 100 * se_firm_cluster)
factor_cols <- c(SMH = okabe[5], NVDA = okabe[7])

p5 <- ggplot(ab, aes(y = spec, xdist = dist_normal(est, se), color = factor, fill = factor)) +
  geom_vline(xintercept = 0, linetype = 2, linewidth = 0.3) +
  stat_halfeye(.width = c(0.5, 0.95), slab_alpha = 0.2, point_size = 1.4,
               position = position_dodge(width = 0.55), normalize = "groups") +
  scale_color_manual(values = factor_cols, name = "AI factor") +
  scale_fill_manual(values = factor_cols, name = "AI factor") +
  labs(x = "Pooled sign-adjusted slope (pp per 100 MW/$bn), 4 events", y = NULL) +
  theme_classic(base_size = 8) +
  theme(legend.position = "bottom")
save_both(p5, "fig5_ai_beta_control", 150, 85)

cat("figures written to", fig, "\n")
