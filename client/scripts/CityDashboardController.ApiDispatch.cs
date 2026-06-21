using Godot;
using System;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private void OnApiRequestFinished(string endpoint, bool success, string jsonBody)
    {
        if (!success)
        {
            HandleTransportError(endpoint, jsonBody);
            return;
        }

        var parsedResponse = DashboardApiResponseParser.Parse(jsonBody);
        if (parsedResponse.Status != DashboardApiResponseParseStatus.Success)
        {
            SetErrorState(
                parsedResponse.Status == DashboardApiResponseParseStatus.Empty
                    ? "Порожня відповідь сервера."
                    : "Сервер повернув пошкоджену відповідь."
            );
            ClearPendingAction(endpoint);
            return;
        }
        var root = parsedResponse.Root;

        if (endpoint == "/api/city/status")
        {
            HandleCityStatus(root);
            return;
        }

        if (TryHandleBuildingFlowResponse(endpoint, root))
        {
            return;
        }

        if (TryHandlePlayerActionResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleBuildingPortfolioResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleBusinessStatusResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleEducationResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleBankResponse(endpoint, root))
        {
            return;
        }

        if (TryHandlePoliceResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleCourtResponse(endpoint, root))
        {
            return;
        }

        if (TryHandlePoliticalResponse(endpoint, root))
        {
            return;
        }

        if (TryHandlePressResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleCasinoResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleShadowResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleLawyerResponse(endpoint, root))
        {
            return;
        }

        if (TryHandleAtelierResponse(endpoint, root))
        {
            return;
        }

        bool apiSuccess = root["success"]?.GetValue<bool>() ?? false;
        string message = root["message"]?.ToString() ?? "";
        var data = root["data"];

        if (!apiSuccess)
        {
            if (endpoint == "/api/player/register")
            {
                _pendingRegistration = false;
                ShowCharacterCreation(LocalizeRegistrationError(message));
                return;
            }

            if (IsSessionError(message))
            {
                HandleInvalidSession(message);
            }
            else
            {
                SetErrorState(BuildActionErrorMessage(endpoint, message));
            }

            if (endpoint == "/api/education/exam/submit")
            {
                _examPanel?.SetSubmitEnabled(true);
            }

            ClearPendingAction(endpoint);
            return;
        }

        ClearPendingAction(endpoint);

        if (endpoint == "/api/player/register" || endpoint.StartsWith("/api/player/"))
        {
            _bootstrapPending = false;
        }
        if (endpoint == "/api/player/register")
        {
            _pendingRegistration = false;
        }

        ClearErrorState();
        SetStatus(message, true);
        UpdateEffectsUI(root["effects"]);
        AddNewsToHistory(data);

        if (data != null && data["username"] != null)
        {
            HideCharacterCreation();
            UpdatePlayerUI(data);
        }

        HandleBuildingFlowSuccess(endpoint, data);

        if (data != null && data["name"] != null && data["treasury_balance"] != null)
        {
            UpdateCityUI(data);
        }

        if (endpoint.StartsWith("/api/jobs/apply"))
        {
            _pendingApply = false;
        }

        if (endpoint == "/api/education/exam/submit")
        {
            string resultMessage = message;
            if (data?["passed"]?.GetValue<bool>() == true)
            {
                resultMessage = $"Іспит здано! {data["score"]}. Тепер доступні кращі вакансії.";
            }

            _examPanel?.ShowResult(resultMessage);
            SetStatus(resultMessage, true);
        }

        UpdateNextActionHint(root["effects"]);
        UpdateGoalUI(root["effects"]);
        UpdateActionButtons();
    }

    private void HandleTransportError(string endpoint, string jsonBody)
    {
        _applyFirstVacancy = false;
        _buyFirstBusiness = false;
        _joinFirstSportsClub = false;
        _pendingApply = false;
        _pendingBusinessMarket = false;
        _pendingSportsClubs = false;
        _pendingExamInfo = false;
        _pendingRefresh = false;
        _pendingBuildingPortfolio = false;
        _pendingBusinessStatus = false;
        _pendingBuildLandCatalog = false;
        _pendingBuildBlueprintCatalog = false;
        _pendingOnboarding = false;
        _pendingRegistration = false;
        _pendingLandBuyKey = "";
        _pendingBuildingApplicationKey = "";
        _pendingBuildingActivationKey = "";
        ClearPendingAction(endpoint);
        _examPanel?.SetSubmitEnabled(true);

        if (endpoint == "/api/player/register")
        {
            ShowCharacterCreation(Tr("CHARACTER_ERROR_SERVER"));
            return;
        }

        if (!string.IsNullOrWhiteSpace(jsonBody))
        {
            try
            {
                var root = JsonNode.Parse(jsonBody);
                string message = root?["message"]?.ToString() ?? "";
                if (!string.IsNullOrEmpty(message))
                {
                    SetErrorState(BuildActionErrorMessage(endpoint, message));
                    UpdateActionButtons();
                    return;
                }
            }
            catch (Exception e)
            {
                GD.PrintErr($"CityDashboardController: error body parse failed: {e.Message}");
            }
        }

        SetErrorState("Backend недоступний. Запусти: .\\scripts\\play.ps1");
        UpdateActionButtons();
    }

    private static bool IsSessionError(string message)
    {
        return message.Contains("Сесія гравця недійсна", StringComparison.Ordinal);
    }

    private void HandleInvalidSession(string message)
    {
        _session?.ClearSession();
        _bootstrapPending = true;
        _hasJob = false;
        _canApplyJob = false;
        _canWork = false;
        _canSleep = false;
        _canEat = false;
        _canBuyBusiness = false;
        _canCollectDividend = false;
        _canJoinSports = false;
        _canTrainSports = false;
        _canTakeExam = false;
        _playerBalance = 0.0;
        _activeAvatar = DashboardActiveAvatarState.Empty;
        UpdateActiveAvatarPresentation();
        ClearBuildingPortfolio();
        ClearBuildFlow();
        SetErrorState(message);
        UpdateActionButtons();
        ShowCharacterCreation(Tr("CHARACTER_ERROR_SESSION"));
    }

    private static string BuildActionErrorMessage(string endpoint, string message)
    {
        if (message.Contains("Недостатньо енергії", StringComparison.Ordinal))
        {
            return $"{message} Натисніть «Спати», щоб відновитись.";
        }

        if (endpoint == "/api/jobs/vacancies")
        {
            return string.IsNullOrWhiteSpace(message) ? "Немає доступних вакансій." : message;
        }

        return string.IsNullOrWhiteSpace(message) ? "Дія не виконана. Спробуйте ще раз." : message;
    }

    private static string BuildActionKey(string action)
    {
        return $"{action}-{Guid.NewGuid():N}";
    }

    private void ClearPendingAction(string endpoint)
    {
        if (endpoint == "/api/player/onboarding/choose")
        {
            _pendingOnboarding = false;
            UpdateOnboardingUi();
        }
        else if (endpoint == "/api/player/onboarding/police-recovery")
        {
            _pendingPoliceRecoveryKey = "";
            UpdatePoliceRecoveryButton();
        }
        else if (ClearPlayerActionPending(endpoint))
        {
            // The feature partial cleared its own pending state.
        }
        else if (endpoint.StartsWith("/api/player/") && endpoint != "/api/player/register" && !IsBuildingPortfolioEndpoint(endpoint) && !endpoint.Contains("/onboarding"))
        {
            _pendingRefresh = false;
        }
        else if (endpoint == "/api/city/status")
        {
            _pendingRefresh = false;
        }
        else if (endpoint.StartsWith("/api/buildings/") && endpoint.EndsWith("/open"))
        {
            _pendingBuildingOpenKey = "";
        }
        else if (endpoint.StartsWith("/api/buildings/") && endpoint.EndsWith("/repair"))
        {
            _pendingBuildingRepairKey = "";
        }
        else if (IsBuildingPortfolioEndpoint(endpoint))
        {
            _pendingBuildingPortfolio = false;
        }
        else if (endpoint == "/api/land/parcels")
        {
            _pendingBuildLandCatalog = false;
        }
        else if (endpoint == "/api/business/blueprints")
        {
            _pendingBuildBlueprintCatalog = false;
        }
        else if (endpoint == "/api/land/buy")
        {
            _pendingLandBuyKey = "";
        }
        else if (endpoint == "/api/building/applications")
        {
            _pendingBuildingApplicationKey = "";
        }
        else if (IsBuildingActivationEndpoint(endpoint))
        {
            _pendingBuildingActivationKey = "";
        }

        UpdateActionButtons();
    }
}
