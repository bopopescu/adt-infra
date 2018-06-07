import traceback

from common.presubmit.constants import Constants
from common.presubmit.sync_presubmit_gerrit_agent import SyncPresubmitGerritAgent

from recipe_engine import recipe_api

class GerritApi(recipe_api.RecipeApi):
  def post(self, agent_lib, message,
                    gerrit_verify_flag=None):  # pragma: no cover
    step_result = self.m.step('Updating Gerrit', [])
    try:
      agent = SyncPresubmitGerritAgent(agent_lib)
      agent.verify(self.m.properties[Constants.CHANGE_ID],
                   self.m.properties[Constants.CHANGE_REVISION],
                   gerrit_verify_flag, message)
    except:  # pragma: no cover
      traceback.print_exc()
      step_result.presentation.status = self.m.step.WARNING
    finally:
      pass