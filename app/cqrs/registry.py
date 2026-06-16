from __future__ import annotations

from app.cqrs.bus import CommandBus, QueryBus
from app.cqrs.handlers.admin import (
    GetAdminStatsHandler,
    GetUserProtocolDraftPdfHandler,
    ListUsersHandler,
    UpdateUserRoleHandler,
)
from app.cqrs.handlers.auth import LoginUserHandler, RegisterUserHandler
from app.cqrs.handlers.dashboard import GetDashboardHandler
from app.cqrs.handlers.exports import (
    CreateExamResultsExportHandler,
    CreateProtocolExportHandler,
    GetExportTaskHandler,
)
from app.cqrs.handlers.manuals import GetManualPathHandler, ListManualsHandler
from app.cqrs.handlers.staff import (
    ExportExamScheduleHandler,
    ListExamScheduleHandler,
    ListKotUsersHandler,
    UpdateKotSafetyGroupHandler,
)
from app.cqrs.handlers.profile import (
    BuildProtocolPdfHandler,
    GetProfileHandler,
    StartAttemptsExportHandler,
    StartProtocolExportHandler,
    UpdateProfileHandler,
)
from app.cqrs.handlers.tests_catalog import CreateTestHandler, ListTestsHandler
from app.cqrs.handlers.tests_editor import (
    AddTicketHandler,
    DeleteTestHandler,
    DeleteTicketHandler,
    GetTestForEditHandler,
    PublishTestHandler,
    SaveTicketHandler,
    UpdateTestSettingsHandler,
)
from app.cqrs.handlers.tests_exam import (
    AbandonExamHandler,
    FinishExamHandler,
    GetExamAttemptResultHandler,
    GetExamSessionHandler,
    OpenExamTicketHandler,
    StartExamSessionHandler,
    SubmitExamTicketAnswersHandler,
)
from app.cqrs.handlers.tests_protocols import (
    GetAttemptProtocolDraftPdfHandler,
    GetAttemptProtocolFormPdfHandler,
    GetSignedProtocolHandler,
    GetSignedProtocolPdfHandler,
    SignProtocolHandler,
)
from app.cqrs.handlers.tests_training import (
    GetTrainingAttemptResultHandler,
    GetTrainingPaperHandler,
    SubmitTrainingHandler,
)
from app.cqrs.handlers.wiki import (
    CreateWikiPageHandler,
    DeleteWikiAttachmentHandler,
    DeleteWikiPageHandler,
    GetWikiAttachmentPathHandler,
    GetWikiPageHandler,
    ListWikiPagesHandler,
    UpdateWikiPageHandler,
)
from app.cqrs.messages.admin import (
    GetAdminStatsQuery,
    GetUserProtocolDraftPdfQuery,
    ListUsersQuery,
    UpdateUserRoleCommand,
)
from app.cqrs.messages.auth import LoginUserCommand, RegisterUserCommand
from app.cqrs.messages.dashboard import GetDashboardQuery
from app.cqrs.messages.exports import (
    CreateExamResultsExportCommand,
    CreateProtocolExportCommand,
    GetExportTaskQuery,
)
from app.cqrs.messages.manuals import GetManualPathQuery, ListManualsQuery
from app.cqrs.messages.staff import (
    ExportExamScheduleQuery,
    ListExamScheduleQuery,
    ListKotUsersQuery,
    UpdateKotSafetyGroupCommand,
)
from app.cqrs.messages.profile import (
    BuildProtocolPdfQuery,
    GetProfileQuery,
    StartAttemptsExportCommand,
    StartProtocolExportCommand,
    UpdateProfileCommand,
)
from app.cqrs.messages.wiki import (
    CreateWikiPageCommand,
    DeleteWikiAttachmentCommand,
    DeleteWikiPageCommand,
    GetWikiAttachmentPathQuery,
    GetWikiPageQuery,
    ListWikiPagesQuery,
    UpdateWikiPageCommand,
)
from app.cqrs.messages.tests import (
    AddTicketCommand,
    CreateTestCommand,
    DeleteTestCommand,
    DeleteTicketCommand,
    PublishTestCommand,
    UpdateTestSettingsCommand,
    AbandonExamCommand,
    FinishExamCommand,
    GetExamAttemptResultQuery,
    GetExamSessionQuery,
    GetAttemptProtocolDraftPdfQuery,
    GetAttemptProtocolFormPdfQuery,
    GetSignedProtocolPdfQuery,
    GetSignedProtocolQuery,
    GetTestForEditQuery,
    GetTrainingAttemptResultQuery,
    GetTrainingPaperQuery,
    ListTestsQuery,
    OpenExamTicketCommand,
    SaveTicketCommand,
    SignProtocolCommand,
    StartExamSessionCommand,
    SubmitExamTicketAnswersCommand,
    SubmitTrainingCommand,
)


def build_command_bus() -> CommandBus:
    bus = CommandBus()
    bus.register(RegisterUserCommand, RegisterUserHandler())
    bus.register(LoginUserCommand, LoginUserHandler())
    bus.register(CreateTestCommand, CreateTestHandler())
    bus.register(AddTicketCommand, AddTicketHandler())
    bus.register(SaveTicketCommand, SaveTicketHandler())
    bus.register(DeleteTicketCommand, DeleteTicketHandler())
    bus.register(DeleteTestCommand, DeleteTestHandler())
    bus.register(UpdateTestSettingsCommand, UpdateTestSettingsHandler())
    bus.register(PublishTestCommand, PublishTestHandler())
    bus.register(SubmitTrainingCommand, SubmitTrainingHandler())
    bus.register(StartExamSessionCommand, StartExamSessionHandler())
    bus.register(OpenExamTicketCommand, OpenExamTicketHandler())
    bus.register(SubmitExamTicketAnswersCommand, SubmitExamTicketAnswersHandler())
    bus.register(AbandonExamCommand, AbandonExamHandler())
    bus.register(FinishExamCommand, FinishExamHandler())
    bus.register(SignProtocolCommand, SignProtocolHandler())
    bus.register(UpdateProfileCommand, UpdateProfileHandler())
    bus.register(UpdateUserRoleCommand, UpdateUserRoleHandler())
    bus.register(UpdateKotSafetyGroupCommand, UpdateKotSafetyGroupHandler())
    bus.register(StartProtocolExportCommand, StartProtocolExportHandler())
    bus.register(StartAttemptsExportCommand, StartAttemptsExportHandler())
    bus.register(CreateExamResultsExportCommand, CreateExamResultsExportHandler())
    bus.register(CreateProtocolExportCommand, CreateProtocolExportHandler())
    bus.register(CreateWikiPageCommand, CreateWikiPageHandler())
    bus.register(UpdateWikiPageCommand, UpdateWikiPageHandler())
    bus.register(DeleteWikiPageCommand, DeleteWikiPageHandler())
    bus.register(DeleteWikiAttachmentCommand, DeleteWikiAttachmentHandler())
    return bus


def build_query_bus() -> QueryBus:
    bus = QueryBus()
    bus.register(ListTestsQuery, ListTestsHandler())
    bus.register(GetTestForEditQuery, GetTestForEditHandler())
    bus.register(GetTrainingPaperQuery, GetTrainingPaperHandler())
    bus.register(GetTrainingAttemptResultQuery, GetTrainingAttemptResultHandler())
    bus.register(GetExamSessionQuery, GetExamSessionHandler())
    bus.register(GetExamAttemptResultQuery, GetExamAttemptResultHandler())
    bus.register(GetSignedProtocolQuery, GetSignedProtocolHandler())
    bus.register(GetSignedProtocolPdfQuery, GetSignedProtocolPdfHandler())
    bus.register(GetAttemptProtocolFormPdfQuery, GetAttemptProtocolFormPdfHandler())
    bus.register(GetAttemptProtocolDraftPdfQuery, GetAttemptProtocolDraftPdfHandler())
    bus.register(GetProfileQuery, GetProfileHandler())
    bus.register(BuildProtocolPdfQuery, BuildProtocolPdfHandler())
    bus.register(GetDashboardQuery, GetDashboardHandler())
    bus.register(ListUsersQuery, ListUsersHandler())
    bus.register(GetAdminStatsQuery, GetAdminStatsHandler())
    bus.register(GetUserProtocolDraftPdfQuery, GetUserProtocolDraftPdfHandler())
    bus.register(ListManualsQuery, ListManualsHandler())
    bus.register(GetManualPathQuery, GetManualPathHandler())
    bus.register(GetExportTaskQuery, GetExportTaskHandler())
    bus.register(ListKotUsersQuery, ListKotUsersHandler())
    bus.register(ListExamScheduleQuery, ListExamScheduleHandler())
    bus.register(ExportExamScheduleQuery, ExportExamScheduleHandler())
    bus.register(ListWikiPagesQuery, ListWikiPagesHandler())
    bus.register(GetWikiPageQuery, GetWikiPageHandler())
    bus.register(GetWikiAttachmentPathQuery, GetWikiAttachmentPathHandler())
    return bus
