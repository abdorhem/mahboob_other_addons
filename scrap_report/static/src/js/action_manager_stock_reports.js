odoo.define('scrap_report.ActionManager', function (require) {
"use strict";

var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');

ActionManager.include({
    /**
     * Overrides to handle the 'ir_actions_stock_report_download' actions.
     *
     * @override
     * @private
     */

    _executeStockReportDownloadAction: function (action, options) {
        var self = this;
        framework.blockUI();
        return new Promise(function (resolve, reject) {
            session.get_file({
                url: '/action_report_print',
                data: action.data,
                success: resolve,
                error: (error) => {
                    self.call('crash_manager', 'rpc_error', error);
                    reject();
                },
                complete: framework.unblockUI,
            });
        });
    },

    _handleAction: function (action, options) {
        if (action.type === 'ir_actions_stock_report_download') {
            return this._executeStockReportDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    },
    // _handleAction: function (action, options) {
    //     if (action.type === 'ir_actions_stock_report_download') {
    //         framework.blockUI();
    //         var def = $.Deferred();

    //         session.get_file({
    //             url: '/action_report_print',
    //             data: action.data,
    //             success: def.resolve.bind(def),
    //             error: function () {
    //                 crash_manager.rpc_error.apply(crash_manager, arguments);
    //                 def.reject();
    //             },
    //             complete: framework.unblockUI,
    //         });
    //         return def;
    //     }
    //     return this._super.apply(this, arguments);
    // },
});

});
