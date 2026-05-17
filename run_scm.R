library(Synth)
library(SCtools)

setwd("/Users/sousekilyu/Documents/Github/taiwan-political-research")

# Load balanced panel (all counties have all years, with NAs for missing)
df <- read.csv("data/merged_panel_balanced.csv", stringsAsFactors = FALSE)
df$year <- as.numeric(df$year)
df$log_income <- as.numeric(df$log_income)
df$per_capita_income <- as.numeric(df$per_capita_income)

# Counties to analyze as treated units
# DPP strongholds (treatment = DPP takeover year):
#   Tainan: DPP since 1997 (treatment year = 1997)
#   Kaohsiung: DPP since 1998
#   Pingtung: DPP since 1993
#   Chiayi County: DPP since 2001
# KMT strongholds (treatment = beginning of period / KMT consolidation):
#   Hualien: KMT throughout (treatment year = 1990, we study "always KMT")
#   Nantou: KMT except 1997-2005 (use 2005 as KMT re-consolidation)
#   Taipei: KMT 1994-2014 (16 years), then IND, then KMT again
#   Miaoli: KMT/IND but non-DPP

# For SCM, treatment year varies by case
# We use log_income as primary outcome
# Predictors: pre-treatment averages of unemployment_rate, log_income

run_scm <- function(treated_county, treatment_year, donor_counties, 
                     start_year = 1990, end_year = 2024,
                     outcome_var = "log_income") {
  
  cat(sprintf("\n===== SCM: %s (treatment=%d) =====\n", treated_county, treatment_year))
  
  # Filter to required years
  sub <- df[df$year >= start_year & df$year <= end_year, ]
  
  # Create unit numbers
  counties <- sort(unique(sub$county))
  unit_map <- setNames(seq_along(counties), counties)
  sub$unit.num <- unit_map[sub$county]
  
  treated_id <- unit_map[treated_county]
  control_ids <- unit_map[setdiff(donor_counties, treated_county)]
  
  if (treated_id %in% control_ids) {
    control_ids <- control_ids[control_ids != treated_id]
  }
  
  # Prepare predictors: pre-treatment averages of key vars
  pre_treatment_years <- start_year:(treatment_year - 1)
  
  if (length(pre_treatment_years) < 3) {
    cat(sprintf("  WARNING: Only %d pre-treatment years. Skipping.\n", length(pre_treatment_years)))
    return(NULL)
  }
  
  # dataprep
  dp <- tryCatch({
    dataprep(
      foo = sub,
      predictors = c("unemployment_rate", "tax_revenue_per_capita"),
      predictors.op = "mean",
      special.predictors = list(
        list("per_capita_income", pre_treatment_years, "mean")
      ),
      dependent = outcome_var,
      unit.variable = "unit.num",
      time.variable = "year",
      treatment.identifier = treated_id,
      controls.identifier = control_ids,
      time.predictors.prior = pre_treatment_years,
      time.optimize.ssr = pre_treatment_years,
      time.plot = start_year:end_year,
      unit.names.variable = "county"
    )
  }, error = function(e) {
    cat(sprintf("  ERROR in dataprep: %s\n", e$message))
    return(NULL)
  })
  
  if (is.null(dp)) return(NULL)
  
  # synth
  synth_out <- tryCatch({
    synth(dp)
  }, error = function(e) {
    cat(sprintf("  ERROR in synth: %s\n", e$message))
    return(NULL)
  })
  
  if (is.null(synth_out)) return(NULL)
  
  # Extract results
  # Treated path
  treated_path <- dp$Z1
  treated_years <- as.numeric(rownames(dp$Z1))
  
  # Synthetic path
  synth_path <- dp$Z0 %*% synth_out$solution.w
  synth_years <- as.numeric(rownames(dp$Z0))
  
  # Align years
  common_years <- intersect(treated_years, synth_years)
  
  # Compute gaps
  gaps <- sapply(common_years, function(y) {
    treated_val <- treated_path[as.character(y), 1]
    synth_val <- synth_path[as.character(y), 1]
    c(year = y, treated = treated_val, synthetic = synth_val, gap = treated_val - synth_val)
  })
  
  gaps_df <- as.data.frame(t(gaps))
  names(gaps_df) <- c("year", "treated", "synthetic", "gap")
  
  # Pre/post MSPE
  pre_gaps <- gaps_df[gaps_df$year < treatment_year, ]
  post_gaps <- gaps_df[gaps_df$year >= treatment_year, ]
  
  pre_msp <- if (nrow(pre_gaps) > 0) mean(pre_gaps$gap^2, na.rm = TRUE) else NA
  post_msp <- if (nrow(post_gaps) > 0) mean(post_gaps$gap^2, na.rm = TRUE) else NA
  ratio <- if (!is.na(pre_msp) && pre_msp > 0) post_msp / pre_msp else NA
  
  # Average post-treatment gap
  avg_gap <- mean(post_gaps$gap, na.rm = TRUE)
  
  # Weights
  weights <- synth_out$solution.w
  donor_names <- colnames(dp$Z0)
  nonzero <- which(weights > 0.01)
  
  result <- list(
    county = treated_county,
    treatment_year = treatment_year,
    gaps = gaps_df,
    avg_gap = avg_gap,
    pre_msp = pre_msp,
    post_msp = post_msp,
    ratio = ratio,
    donor_weights = data.frame(
      donor = donor_names[nonzero],
      weight = weights[nonzero]
    ),
    weights = weights
  )
  
  cat(sprintf("  Avg post-treatment gap: %.4f\n", avg_gap))
  cat(sprintf("  Ratio post/pre MSPE: %.2f\n", ratio))
  cat(sprintf("  Donors with >1%% weight:\n"))
  for (i in seq_len(nrow(result$donor_weights))) {
    cat(sprintf("    %s: %.3f\n", result$donor_weights$donor[i], 
                result$donor_weights$weight[i]))
  }
  
  return(result)
}

# ============================================
# Define expanded cases
# ============================================

all_counties <- sort(unique(df$county))
# Remove Kinmen, Lienchiang
all_counties <- all_counties[!all_counties %in% c("金門縣", "連江縣")]
cat(sprintf("Total counties: %d\n", length(all_counties)))

# DPP long-term strongholds
dpp_cases <- list(
  list(county = "臺南市", start = 1997, label = "Tainan (DPP)"),
  list(county = "高雄市", start = 1998, label = "Kaohsiung (DPP)"),
  list(county = "屏東縣", start = 1993, label = "Pingtung (DPP)"),
  list(county = "嘉義縣", start = 2001, label = "Chiayi County (DPP)"),
  list(county = "宜蘭縣", start = 1989, label = "Yilan (DPP 1989-2005)")  # long DPP run then alternation
)

# KMT long-term strongholds
kmt_cases <- list(
  list(county = "花蓮縣", start = 1990, label = "Hualien (KMT)"),
  list(county = "南投縣", start = 2005, label = "Nantou (KMT re-consolidation)"),
  list(county = "臺北市", start = 1998, label = "Taipei (KMT 1998-2014)"),
  list(county = "苗栗縣", start = 2005, label = "Miaoli (KMT)"),
  list(county = "臺東縣", start = 1990, label = "Taitung (KMT/PFP)"),
  list(county = "新竹縣", start = 2001, label = "Hsinchu County (KMT since 2001)")
)

# Run SCM for all cases
all_results <- list()
case_info <- list()

for (case in dpp_cases) {
  res <- run_scm(case$county, case$start, all_counties)
  if (!is.null(res)) {
    res$party <- "DPP"
    res$label <- case$label
    all_results[[length(all_results) + 1]] <- res
  }
}

for (case in kmt_cases) {
  res <- run_scm(case$county, case$start, all_counties)
  if (!is.null(res)) {
    res$party <- "KMT"
    res$label <- case$label
    all_results[[length(all_results) + 1]] <- res
  }
}

# ============================================
# Build summary table
# ============================================
summary_rows <- list()
for (r in all_results) {
  summary_rows[[length(summary_rows) + 1]] <- data.frame(
    county = r$county,
    label = r$label,
    party = r$party,
    treatment_year = r$treatment_year,
    avg_gap = round(r$avg_gap, 4),
    pre_msp = round(r$pre_msp, 4),
    post_msp = round(r$post_msp, 4),
    ratio = round(r$ratio, 2),
    stringsAsFactors = FALSE
  )
}
summary_df <- do.call(rbind, summary_rows)

# Save results
saveRDS(all_results, "data/scm_results.rds")
write.csv(summary_df, "data/scm_summary.csv", row.names = FALSE, fileEncoding = "UTF-8")

cat("\n===== SCM COMPLETE =====\n")
cat(sprintf("Successfully analyzed %d cases\n", length(all_results)))
print(summary_df)

# ============================================
# Generate SCM path plots
# ============================================
pdf("results/scm_all_paths.pdf", width = 14, height = 20)
par(mfrow = c(ceiling(length(all_results)/2), 2), mar = c(3,3,3,1), mgp = c(2,0.5,0))

for (r in all_results) {
  g <- r$gaps
  party_color <- ifelse(r$party == "DPP", "#1B9431", "#0052A5")  # DPP green, KMT blue
  
  y_range <- range(c(g$treated, g$synthetic), na.rm = TRUE)
  
  plot(g$year, g$treated, type = "l", lwd = 2, col = party_color,
       xlab = "Year", ylab = "Log per capita income",
       main = sprintf("%s\n(Treatment: %d)", r$label, r$treatment_year),
       ylim = y_range, cex.main = 0.9)
  lines(g$year, g$synthetic, type = "l", lwd = 2, col = "gray50", lty = 2)
  abline(v = r$treatment_year - 0.5, lty = 3, col = "red")
  legend("topleft", legend = c("Actual", "Synthetic"), 
         col = c(party_color, "gray50"), lty = c(1, 2), lwd = 2, 
         cex = 0.7, bty = "n")
}

dev.off()
cat("Saved: results/scm_all_paths.pdf\n")

# Gap plots
pdf("results/scm_all_gaps.pdf", width = 14, height = 20)
par(mfrow = c(ceiling(length(all_results)/2), 2), mar = c(3,3,3,1), mgp = c(2,0.5,0))

for (r in all_results) {
  g <- r$gaps
  party_color <- ifelse(r$party == "DPP", "#1B9431", "#0052A5")
  
  plot(g$year, g$gap, type = "h", lwd = 2, col = ifelse(g$gap > 0, party_color, "red"),
       xlab = "Year", ylab = "Gap (Actual - Synthetic)",
       main = sprintf("%s Gap\n(Avg post: %.4f)", r$label, r$avg_gap),
       cex.main = 0.9)
  abline(h = 0, lty = 2, col = "gray50")
  abline(v = r$treatment_year - 0.5, lty = 3, col = "black")
}

dev.off()
cat("Saved: results/scm_all_gaps.pdf\n")
