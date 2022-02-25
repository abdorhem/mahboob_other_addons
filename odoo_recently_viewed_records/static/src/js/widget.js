odoo.define('odoo_recently_viewed_records.widget', function (require) {
    "use strict";
    
    var core = require('web.core');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var web_client = require('web.web_client');
    var QWeb = core.qweb;
    var _t = core._t;

    
    var RecentRecord = Widget.extend({
        template:'odoo_recently_viewed_records.RecentRecord',
        events: {
            // "click": "_onRecordMenuClick",
            "click .o_mail_channel_preview": "_onRecordFilterClick",
        },
        start: function () {
            this.$records_preview = this.$('.o_mail_systray_dropdown_items');
            this._updateRecordPreview();
            return this._super();
        },
        is_open: function () {
            return this.$el.hasClass('open');
        },
            start: function () {
                this.$records_preview = this.$('.o_mail_navbar_dropdown_channels');
                this._updateRecordPreview();
                return this._super();
            },
        
            // Private
        
            /**
             * Make RPC and get current user's activity details
             * @private
             */
            _getRecordData: function(){
                var self = this;
                return ajax.jsonRpc("/get/recently/view/records", 'call', {}).then(
                    function(data) {
                        self.records = data;
                        
                        }
                        
                    );
            },
            // /**
            //  * Get particular model view to redirect on click of activity scheduled on that model.
            //  * @private
            //  * @param {string} model
            //  */
            _getActivityModelViewID: function (model) {
                return this._rpc({
                    model: model,
                    method: 'get_activity_view_id'
                });
            },
            /**
             * Check wether activity systray dropdown is open or not
             * @private
             * @returns {boolean}
             */
            _isOpen: function () {
                return this.$el.hasClass('open');
            },
            /**
             * Update(render) activity system tray view on activity updation.
             * @private
             */
            _updateRecordPreview: function () {
                var self = this;
                self._getRecordData().then(function (){
                    self.$records_preview.html(QWeb.render('odoo_recently_viewed_records.RecentRecordPreview', {
                        records : self.records
                    }));
                });
            },
            
        
        
            // Handlers
        
            /**
             * Redirect to particular model view
             * @private
             * @param {MouseEvent} event
             */
            _onRecordFilterClick: function (event) {
                // fetch the data from the button otherwise fetch the ones from the parent (.o_mail_channel_preview).
                var data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
                var context = {};
                this.do_action({


                    type: 'ir.actions.act_window',
                    name: data.model_name,
                    res_model:  data.res_model,
                    res_id:  data.res_id,
                    views: [[false, 'form']],
                    search_view_id: [false],
                    context:context,
                    target:'current',
                });
            },
            /**
             * When menu clicked update activity preview if counter updated
             * @private
             * @param {MouseEvent} event
             */
    
            _onRecordMenuClick: function (event) {
            event.preventDefault();
            if (!this.is_open()) {
                this._updateRecordPreview();  // we are opening the dropdown so update its content
            }
        },
    });
    
    SystrayMenu.Items.push(RecentRecord);

    
    });