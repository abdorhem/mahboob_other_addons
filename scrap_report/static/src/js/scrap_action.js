odoo.define('scrap_report.scrap_action', function (require) {
'use strict';

var core = require('web.core');
var Context = require('web.Context');
var Dialog = require('web.Dialog');
var AbstractAction = require('web.AbstractAction');
var datepicker = require('web.datepicker');
var session = require('web.session');
var field_utils = require('web.field_utils');
var RelationalFields = require('web.relational_fields');
var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
var WarningDialog = require('web.CrashManager').WarningDialog;
var Widget = require('web.Widget');
var Pager = require('web.Pager');
const { ComponentWrapper } = require('web.OwlCompatibility');
var QWeb = core.qweb;
const _t = core._t;


var M2MFilters = Widget.extend(StandaloneFieldManagerMixin, {

    init: function (parent, fields) {
        this._super.apply(this, arguments);
        StandaloneFieldManagerMixin.init.call(this);
        this.fields = fields;
        this.widgets = {};
    },

    willStart: function () {
        var self = this;
        var defs = [this._super.apply(this, arguments)];
        _.each(this.fields, function (field, fieldName) {
            defs.push(self._makeM2MWidget(field, fieldName));
        });
        return $.when.apply($, defs);
    },

    start: function () {
        var self = this;
        _.each(this.fields, function (field, fieldName) {
            self.$el.append($('<p/>', {style: 'font-weight:bold;'}).text(field.label));
            self.widgets[fieldName].appendTo(self.$el);
        });
        return this._super.apply(this, arguments);
    },

    _confirmChange: function () {
        var self = this;
        var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
        var data = {};
        _.each(this.fields, function (filter, fieldName) {
            data[fieldName] = self.widgets[fieldName].value.res_ids;
        });
        this.trigger_up('m2m_value_changed', data);
        return result;
    },

    _makeM2MWidget: function (fieldInfo, fieldName) {
        var self = this;
        var options = {};
        options[fieldName] = {
            options: {
                no_create_edit: true,
                no_create: true,
            }
        };
        return this.model.makeRecord(fieldInfo.modelName, [{
            fields: [{
                name: 'id',
                type: 'integer',
            }, {
                name: 'display_name',
                type: 'char',
            }],
            name: fieldName,
            relation: fieldInfo.modelName,
            type: 'many2many',
            value: fieldInfo.value,
            domain: fieldInfo.domain
        }], options).then(function (recordID) {
            self.widgets[fieldName] = new RelationalFields.FieldMany2ManyTags(self,
                fieldName,
                self.model.get(recordID),
                {mode: 'edit',}
            );
            self._registerWidget(recordID, fieldName, self.widgets[fieldName]);
        });
    },
});

var ScrapReportAction = AbstractAction.extend({
    hasControlPanel: true,
    custom_events: {
        'm2m_value_changed': function(ev) {
            var self = this;
            var key = _.keys(ev.data)[0];
            self.search_filters[key] = ev.data[key];
            return self.reload().then(function () {
                self.$searchview_buttons.find('.stock_' + key + '_filter').click();
            });
        },
    },

    events:{
        'click .o_product_link': 'open_product',
        'click .o_scrap_transfer_link': 'open_scrap_transfer',
    },

    init: function(parent, action) {
        this.actionManager = parent;
        this.report_model = action.context.model;
        if (this.report_model === undefined) {
            this.report_model = 'scrap.report';
        }
        if (action.context.id) {
            this.inv_movement_report_id = action.context.id;
        }
        this.odoo_context = action.context;
        this.search_options = {};
        this.pagerState = { //default pager options
                limit: 80,
                offset: 0,
            };
        this.search_filters = this._buildSearchFilters();
        if (sessionStorage.getItem('scrap_report_option_session')) {
            this.search_filters = JSON.parse(sessionStorage.getItem('scrap_report_option_session')) || this.search_filters;
        }
        this.M2MFilters = {};
        return this._super.apply(this, arguments);
    },
    start: function() {
        var self = this;
        return $.when(self.get_html(), this._super.apply(this, arguments)).then(function() {
            self.render();
        });
    },
    open_product: function(e){
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "product.product",
            res_id: parseInt($(e.target).data('product')),
            views: [[false, 'form']],
        });
    },
    open_scrap_transfer: function(e){
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "stock.picking",
            res_id: parseInt($(e.target).data('picking_id')),
            views: [[false, 'form']],
        });
    },

    get_html: function() {
        var self = this;
        return this._rpc({
            model: 'scrap.report',
            method: 'get_html',
            args: [self.search_filters, self.pagerState],
            kwargs: {context: session.user_context},
        })
        .then(function (result) {
            return self.parseReportsInformations(result);
        });
    },
    parseReportsInformations: function(values) {
        this.html = values.html;
        this.buttons = values.buttons;
        this.search_options = values.search_options;
        this.search_filters = values.search_filters;
        this.records_count = values.records_count;
        this.pagerState = values.pagerState;
        // this.pagerState.limit = values.limit_per_page;
        this.persist_options();
    },
    persist_options: function() {
        sessionStorage.setItem('scrap_report_option_session', JSON.stringify(this.search_filters));
    },
    render: function() {
        var self = this;
        // self.$el.html(self.html);
        self.update_cp();
        self.$el.find('.o_content').html(self.html)
    },
    reload: function() {
        var self = this;
        return self.get_html().then(function() {
            self.render();
        });
    },
    _shouldRenderPager: function (currentMinimum, limit, size) {
        if (!limit || !size) {
            return false;
        }
        const maximum = Math.min(currentMinimum + limit - 1, size);
        const singlePage = (1 === currentMinimum) && (maximum === size);
        return !singlePage;
    },
    _renderGroupPager: function (group, target) {
        const currentMinimum = this.pagerState.offset + 1;
        const limit = this.pagerState.limit;
        const size = this.records_count;
        if (!this._shouldRenderPager(currentMinimum, limit, size)) {
            return;
        }
        const pager = new ComponentWrapper(this, Pager, { currentMinimum, limit, size });
        const pagerMounting = pager.mount(target).then(() => {
            // Event binding is done here to get the related group and wrapper.
            pager.el.addEventListener('pager-changed', ev => this._onPagerChanged(ev, group));
            // Prevent pager clicks to toggle the group.
            pager.el.addEventListener('click', ev => ev.stopPropagation());
        });
        this.defs.push(pagerMounting);
        this.pagers.push(pager);
    },
    update_cp: function() {
        var self = this;
        if (!this.$buttons) {
            this.renderButtons();
        }
        self.render_searchview_buttons();
        var $pager = this._renderGroupPager();
        return this.updateControlPanel({
            cp_content: {
                $buttons: this.$buttons,
                $searchview_buttons: this.$searchview_buttons,
                $pager: $pager
            },
        });
    },
    do_show: function() {
        this._super();
        this.update_cp();
    },
    _renderGroupButton: function (list, node) {
        var $button = viewUtils.renderButtonFromNode(node, {
            extraClass: node.attrs.icon ? 'o_icon_button' : undefined,
            textAsTitle: !!node.attrs.icon,
        });
        this._handleAttributes($button, node);
        this._registerModifiers(node, list.groupData, $button);

        // TODO this should be moved to event handlers
        $button.on("click", this._onGroupButtonClicked.bind(this, list.groupData, node));
        $button.on("keydown", this._onGroupButtonKeydown.bind(this));

        return $button;
    },
    _renderGroupButtons: function (list, group) {
        var self = this;
        var $buttons = $();
        if (list.value) {
            // buttons make no sense for 'Undefined' group
            group.arch.children.forEach(function (child) {
                if (child.tag === 'button') {
                    $buttons = $buttons.add(self._renderGroupButton(list, child));
                }
            });
        }
        return $buttons;
    },
    renderButtons: function() {
        var $buttons = this._renderGroupButtons(this);
        this.$buttons = $(QWeb.render("ScrapReports.buttons", {buttons: this.buttons}));
        if ($buttons.length) {
            var $buttonSection = $('<div>', {
                class: 'o_group_buttons',
            }).append($buttons);
            $th.append($buttonSection);
        }
        var self = this;
        // this.$buttons = $(QWeb.render("ScrapReports.buttons", {buttons: this.buttons}));
        // // bind actions
        // _.each(this.$buttons.siblings('button'), function(el) {
        //     $(el).click(function() {
        //         return self._rpc({
        //             model: self.report_model,
        //             method: $(el).attr('action'),
        //             args: [self.inv_movement_report_id, self.search_filters],
        //             context: self.odoo_context,
        //         })
        //         .then(function(result){
        //             return self.do_action(result);
        //         });
        //     });
        // });
        _.each(this.$buttons.siblings('button'), function(el) {
            
            $(el).click(function() {
                return self._rpc({                                                                                                                                                                                                                  
                    model: 'scrap.report',
                    method: $(el).attr('action'),
                    args: [self.inv_movement_report_id, self.search_filters],
                    context: self.odoo_context,
                })
                .then(function(result){
                    return self.do_action(result);
                });
            });
        });
        return this.$buttons;
    },
    render_searchview_buttons: function() {
        var self = this;

        this.$searchview_buttons = $(QWeb.render("ScrapReports.searchOptions", {options: self.search_options, filters: self.search_filters}));
        // bind searchview buttons/filter to the correct actions

        this.$searchview_buttons.find('.js_account_reports_status').select2();
        if (self.search_filters.status) {
            self.$searchview_buttons.find('[data-filter="status"]').select2("val",
             self.search_filters.status);
        }
        this.$searchview_buttons.find('.js_account_reports_status').on('change',

        function(e){
            self.search_filters.status = self.$searchview_buttons.find('[data-filter="status"]').val();
            return self.reload().then(function(){
                self.$searchview_buttons.find('.status_filter').click();
            })
        });
        var $datetimepickers = this.$searchview_buttons.find('.js_stock_reports_datetimepicker');
        var options = { // Set the options for the datetimepickers
            locale : moment.locale(),
            format : 'L',
            icons: {
                date: "fa fa-calendar",
            },
        };
        // attach datepicker
        $datetimepickers.each(function () {
            var name = $(this).find('input').attr('name');
            var defaultValue = $(this).data('default-value');
            $(this).datetimepicker(options);
            var dt = new datepicker.DateWidget(options);
            dt.replace($(this)).then(function () {
                dt.$el.find('input').attr('name', name);
                if (defaultValue) { // Set its default value if there is one
                    dt.setValue(moment(defaultValue));
                }
            });
        });
        // format date that needs to be show in user lang
        _.each(this.$searchview_buttons.find('.js_format_date'), function(dt) {
            var date_value = $(dt).html();
            $(dt).html((new movement(date_value)).format('ll'));
        });
        // fold all menu
        this.$searchview_buttons.find('.js_foldable_trigger').click(function (event) {
            $(this).toggleClass('o_closed_menu o_open_menu');
            self.$searchview_buttons.find('.o_foldable_menu[data-filter="'+$(this).data('filter')+'"]').toggleClass('o_closed_menu o_open_menu');
        });
        this.$searchview_buttons.find('.js_stock_report_date_filter').click(function (event) {
            self.search_filters.date.filter = $(this).data('filter');
            var error = false;
            if ($(this).data('filter') === 'custom') {
                var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from"]');
                var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to"]');
                if (date_from.length > 0){
                    error = date_from.val() === "" || date_to.val() === "";
                    self.search_filters.date.date_from = field_utils.parse.date(date_from.val());
                    self.search_filters.date.date_to = field_utils.parse.date(date_to.val());
                }
                else {
                    error = date_to.val() === "";
                }
            }
            if (error) {
                crash_manager.show_warning({data: {message: _t('Date cannot be empty')}});
            } else {
                self.reload();
            }
        });
        _.each(this.search_options.m2m_filters, function(option) {
            if (!self.M2MFilters[option.field]) {
                var fields = {};
                fields[option.field] = {
                    label: option.label,
                    modelName: option.model,
                    // value: self.search_filters[option.field].map(Number),
                    domain: option.domain
                };
                if (!_.isEmpty(fields)) {
                    self.M2MFilters[option.field] = new M2MFilters(self, fields);
                    self.M2MFilters[option.field].appendTo(self.$searchview_buttons.find('.js_stock_' + option.field + '_m2m'));
                }
            } else {
                self.$searchview_buttons.find('.js_stock_' + option.field + '_m2m').append(self.M2MFilters[option.field].$el);
            }
        });

        _.each(this.$searchview_buttons.find('.js_switch_choice_filter'), function(k) {
            $(k).toggleClass('selected', ''+self.search_filters[$(k).data('field')] === ''+$(k).data('id'));
        });

        this.$searchview_buttons.find('.js_switch_choice_filter').click(function (event) {
            self.search_filters[$(this).data('field')] = $(this).data('id');
            self.reload();
        });

        this.$searchview_buttons.find('#clear_filter_scrap_report').on('click',
        function(ev){
            self.search_filters ={
                        'date': {'filter': 'today', 'date_from': '', 'date_to': ''},
            'company_id': NaN,
            'products': [],
            'categories': [],
            'outlets': [],
            'customers': [],



                    }
            self.reload()
            window.location.reload();
        });

    },
    _buildSearchFilters: function () {
        return {
            'date': {'filter': 'today', 'date_from': '', 'date_to': ''},
            'company_id': NaN,
            'products': [],
            'categories': [],
            'outlets': [],
            'branch':[],
            'region':[],

        }
    },
});

core.action_registry.add("scrap_report", ScrapReportAction);
return ScrapReportAction;
});
