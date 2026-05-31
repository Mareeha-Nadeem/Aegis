/**
 * Send telemetry data when a Click Group is clicked, if the clicked element
 * is not the target/anchor/button itself.
 */
(() => {
  const ACTION_TYPES = {
    LEFT_CLICK: 'CL'
  };

  const EventName = {
    CLICK: 'click'
  };

  let analytics = null;

  /**
   * Get dataBi attributes from an element's dataset
   * @param {HTMLElement} element - The element to get dataBi attributes from
   * @returns {Object} - An object containing the dataBi attributes
   */
  const getDataBi = (element) => {
    if (!element || !element.dataset) {
      return {};
    }

    return Object.fromEntries(
      Object.entries(element.dataset)
        .filter(([key]) => key.startsWith('bi') && key.charAt(2) === key.charAt(2).toUpperCase())
        .map(([key, value]) => [
          key.charAt(2).toLowerCase() + key.slice(3),
          value
        ])
    );
  };

  /**
   * Send telemetry data to the analytics plugin
   * @param {string} behaviorId - The behavior ID
   * @param {string} actionType - The action type
   * @param {Object} contentTags - The content tags
   */
  const sendTelemetry = (behaviorId, actionType, contentTags) => {
    const overrides = {
      behavior: behaviorId,
      actionType: actionType,
      contentTags: contentTags
    };
    analytics.capturePageAction(null, overrides);
  };

  /**
   * Run the script.
   */
  const run = () => {
    if (!window.telemetry?.webAnalyticsPlugin || !window.mwf?.ClickGroup) {
      return;
    }

    analytics = telemetry.webAnalyticsPlugin;

    const clickGroupInstances = window.mwf.ClickGroup.getInstances();

    if (!clickGroupInstances?.length) {
      return;
    }

    clickGroupInstances.forEach(clickGroup => {
      const target = clickGroup.target;
      if (!target) {
        return;
      }

      const dataBiObj = getDataBi(target);

      if (Object.keys(dataBiObj).length === 0) {
        return;
      }

      const actionType = ACTION_TYPES.LEFT_CLICK;
      const { bhvr = '0', ...dataBiObjWithoutBhvr } = dataBiObj;

      const handleClickGroupClick = (event) => {
        if (event.target === target) {
          return;
        }

        sendTelemetry(bhvr, actionType, dataBiObjWithoutBhvr);
      };
      clickGroup.el.addEventListener(EventName.CLICK, handleClickGroupClick);
    });
  };

  if (document.readyState !== 'loading') {
    run();
  } else {
    document.addEventListener('DOMContentLoaded', run);
  }
})();
