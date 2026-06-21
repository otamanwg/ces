using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
	private void UpdatePlayerUI(JsonNode data)
	{
		var snapshot = DashboardPlayerSnapshot.FromJson(data);

		if (UsernameLabel != null)
		{
			UsernameLabel.Text = snapshot.Username;
		}

		_playerBalance = snapshot.Balance;
		if (BalanceLabel != null)
		{
			BalanceLabel.Text = $"{snapshot.Balance:N2} ₴";
		}

		if (EducationLabel != null)
		{
			_playerEducation = snapshot.EducationLevel;
			EducationLabel.Text = _playerEducation;
		}

		if (CurrentJobLabel != null)
		{
			CurrentJobLabel.Text = snapshot.Job;
			_hasJob = snapshot.HasJob;
		}

		if (CurrentHostelLabel != null)
		{
			CurrentHostelLabel.Text = snapshot.Hostel;
		}

		if (OwnedBusinessLabel != null)
		{
			_ownedBusinessId = snapshot.OwnedBusinessId;
			OwnedBusinessLabel.Text = snapshot.OwnedBusinessText;
		}

		if (SportsLabel != null)
		{
			SportsLabel.Text = snapshot.SportsText;
		}

		if (EnergyBar != null)
		{
			EnergyBar.Value = snapshot.Energy;
		}

		if (MoodBar != null)
		{
			MoodBar.Value = snapshot.Mood;
		}

		if (HungerBar != null)
		{
			HungerBar.Value = snapshot.Hunger;
		}

		UpdateAvailableActions(snapshot.Actions);
		_tutorialAgeGroup = snapshot.TutorialAgeGroup;
		_onboardingState = snapshot.Onboarding;
		_activeAvatar = DashboardActiveAvatarState.FromSnapshot(snapshot);
		UpdateActiveAvatarPresentation();
		UpdateOnboardingUi();
		UpdatePoliceRecoveryButton();
		if (!string.IsNullOrEmpty(snapshot.Id))
		{
			_session?.SetPlayer(snapshot.Id, snapshot.Username, snapshot.AuthToken);
			if (snapshot.Onboarding.Completed)
			{
				RefreshBuildingPortfolio();
				RefreshBuildCatalog();
				RefreshBusinessStatus();
			}
		}

		UpdateActionButtons();
	}

	private void UpdateAvailableActions(JsonNode actions)
	{
		if (actions == null)
		{
			_canApplyJob = true;
			_canWork = _hasJob;
			_canSleep = true;
			_canEat = false;
			_canBuyBusiness = false;
			_canCollectDividend = false;
			_canJoinSports = true;
			_canTrainSports = false;
			_canTakeExam = _playerEducation == "High School";
			return;
		}

		_canApplyJob = actions["can_apply_job"]?.GetValue<bool>() ?? false;
		_canWork = actions["can_work"]?.GetValue<bool>() ?? false;
		_canSleep = actions["can_sleep"]?.GetValue<bool>() ?? false;
		_canEat = actions["can_eat"]?.GetValue<bool>() ?? false;
		_canBuyBusiness = actions["can_buy_business"]?.GetValue<bool>() ?? false;
		_canCollectDividend = actions["can_collect_dividend"]?.GetValue<bool>() ?? false;
		_canJoinSports = actions["can_join_sports"]?.GetValue<bool>() ?? false;
		_canTrainSports = actions["can_train_sports"]?.GetValue<bool>() ?? false;
		_canTakeExam = actions["can_take_exam"]?.GetValue<bool>() ?? false;
	}

	private void UpdateCityUI(JsonNode data)
	{
		if (CityNameLabel != null)
		{
			CityNameLabel.Text = data["name"]?.ToString() ?? "Місто";
		}

		if (TreasuryLabel != null)
		{
			double treasury = data["treasury_balance"]?.GetValue<double>() ?? 0.0;
			TreasuryLabel.Text = $"{treasury:N2} ₴";
		}

		if (InflationLabel != null)
		{
			double inflation = data["inflation_rate"]?.GetValue<double>() ?? 0.0;
			InflationLabel.Text = $"{inflation:F1}%";
		}
	}

	private void UpdateNextActionHint(JsonNode effects)
	{
		if (NextActionLabel == null || effects == null)
		{
			return;
		}

		foreach (var effect in effects.AsArray())
		{
			if (effect?["key"]?.ToString() != "next_action")
			{
				continue;
			}

			string value = effect["value"]?.ToString() ?? "—";
			string delta = effect["delta"]?.ToString() ?? "";
			NextActionLabel.Text = string.IsNullOrEmpty(delta)
				? $"Що робити зараз: {value}"
				: $"Що робити зараз: {value} ({delta})";
			return;
		}

		NextActionLabel.Text = "Що робити зараз: —";
	}

	private void UpdateGoalUI(JsonNode effects)
	{
		if (GoalLabel == null || effects == null)
		{
			return;
		}

		foreach (var effect in effects.AsArray())
		{
			string key = effect?["key"]?.ToString() ?? "";
			if (key == "goal_manager_cert")
			{
				GoalLabel.Text = $"Ціль: {effect["label"]} — {effect["value"]} ({effect["delta"]})";
				if (GoalProgressBar != null)
				{
					string pctText = effect["value"]?.ToString()?.Replace("%", "") ?? "0";
					if (double.TryParse(pctText, out double pct))
					{
						GoalProgressBar.Value = pct;
					}
				}

				return;
			}

			if (key == "goal_better_job")
			{
				GoalLabel.Text = $"Ціль: {effect["label"]} — {effect["value"]}";
				if (GoalProgressBar != null)
				{
					GoalProgressBar.Value = 100;
				}

				return;
			}

			if (key == "goal_first_business" || key == "goal_business_owner")
			{
				GoalLabel.Text = $"Ціль: {effect["label"]} — {effect["value"]} ({effect["delta"]})";
				if (GoalProgressBar != null)
				{
					if (key == "goal_business_owner")
					{
						GoalProgressBar.Value = 100;
					}
					else
					{
						string pctText = effect["value"]?.ToString()?.Replace("%", "") ?? "0";
						if (double.TryParse(pctText, out double pct))
						{
							GoalProgressBar.Value = pct;
						}
					}
				}

				return;
			}
		}
	}

	private void UpdateEffectsUI(JsonNode effects)
	{
		if (EffectsLabel == null || effects == null)
		{
			return;
		}

		var parts = new List<string>();
		foreach (var effect in effects.AsArray())
		{
			string key = effect?["key"]?.ToString() ?? "";
			if (key == "next_action" || key.StartsWith("stability_"))
			{
				continue;
			}

			string label = effect?["label"]?.ToString();
			string value = effect?["value"]?.ToString();
			if (!string.IsNullOrEmpty(label))
			{
				parts.Add($"{label}: {value}");
			}
		}

		EffectsLabel.Text = parts.Count > 0 ? "Наслідки: " + string.Join(" | ", parts) : "";
	}
}
