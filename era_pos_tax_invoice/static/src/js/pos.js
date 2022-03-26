odoo.define('era_tax_invoice.OrderReceipt', function(require) {
    'use strict';

    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');

//    models.load_fields('pos.config',['allow_qr_code']);

    var module = require('point_of_sale.models');
    var models = module.PosModel.prototype.models;
    for(var i=0; i<models.length; i++){
        var model=models[i];
        if(model.model === 'res.company'){
             model.fields.push('street');
             model.fields.push('city');
             model.fields.push('state_id');
             model.fields.push('country_id');
        }
    }

    var OrderSuper = module.Order;
	module.Order = module.Order.extend({
	    export_for_printing: function(){
			var json = OrderSuper.prototype.export_for_printing.call(this);
			console.log(json);
			return json;
		},
	})
    const PosQRCodeOrderReceipt = OrderReceipt =>
        class extends OrderReceipt {

            get receiptEnv () {
                let receipt_render_env = super.receiptEnv;
                let order = this.env.pos.get_order();
                receipt_render_env.receipt.company.street = this.env.pos.company.street;

                function decimalToHex(rgb) {
                      var hex = Number(rgb).toString(16);
                      if (hex.length < 2) {
                           hex = "0" + hex;
                      }
                      return hex;
                    };

                function ascii_to_hexa(str)
                  {
                    var arr1 = [];
                    str = btoa(unescape(encodeURIComponent((str))));
                    str = atob(str);
                    for (var n = 0, l = str.length; n < l; n ++)
                     {
                        var hex = Number(str.charCodeAt(n)).toString(16);
                        arr1.push(hex);
                     }
                    return arr1.join('');
                   }

                function hexToBase64(hexstring) {
                    return btoa(hexstring.match(/\w{2}/g).map(function(a) {
                        return String.fromCharCode(parseInt(a, 16));
                    }).join(""));
                }

                var hex_seller = ascii_to_hexa(this.env.pos.company.name);
                var len_seller = decimalToHex(hex_seller.length/2);
                var seller_name = "01"+ len_seller + hex_seller;

                var len_seller_vat = decimalToHex(this.env.pos.company.vat.length);
                var seller_vat_no = "02"+ len_seller_vat + ascii_to_hexa(this.env.pos.company.vat);

                var date_time_tz = new Date(order.creation_date - order.creation_date.getTimezoneOffset()*60*1000).toISOString();
                var len_date = decimalToHex(date_time_tz.length);
                var dateTime = String(date_time_tz)
                var order_date = "03"+ len_date + ascii_to_hexa(dateTime);

                var total_with_vat = Math.round(order.get_total_with_tax()*100)/100;
                var len_total = decimalToHex(String(total_with_vat).length);
                var totalWithVatHex = "04"+ len_total + ascii_to_hexa(String(total_with_vat));

                var total_vat = Math.round(order.get_total_tax()*100)/100;
                var len_total_vat = decimalToHex(String(total_vat).length);
                var totalVatHex = "05"+ len_total_vat + ascii_to_hexa(String(total_vat));

                let qrCodeValueHex = seller_name+seller_vat_no+order_date+totalWithVatHex+totalVatHex
                let qrCodeBase64 = hexToBase64(qrCodeValueHex)
                console.log(order);

                var company_address =  this.env.pos.company.street;
                if (this.env.pos.company.city){company_address += "-"+this.env.pos.company.city}
                var company_state = this.env.pos.company.state_id[1];
                if (this.env.pos.company.country_id){company_state += "-"+this.env.pos.company.country_id[1]}
                receipt_render_env.receipt.qr_code = qrCodeBase64;
                receipt_render_env.receipt.company_address = company_address;
                receipt_render_env.receipt.company_state = company_state;
                return receipt_render_env;
            }
        };

    Registries.Component.extend(OrderReceipt, PosQRCodeOrderReceipt);
    return OrderReceipt;
});
