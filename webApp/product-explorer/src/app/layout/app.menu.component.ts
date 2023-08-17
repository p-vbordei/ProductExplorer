import { OnInit } from '@angular/core';
import { Component } from '@angular/core';
import { LayoutService } from './service/app.layout.service';

@Component({
    selector: 'app-menu',
    templateUrl: './app.menu.component.html'
})
export class AppMenuComponent implements OnInit {

    model: any[] = [];

    constructor(public layoutService: LayoutService) { }

    ngOnInit() {
        this.model = [
            {
                label: 'Investigation',
                items: [
                    { label: 'Home', icon: 'pi pi-fw pi-home', routerLink: ['/'] },
                    // { label: 'Product Explorer', icon: 'pi pi-fw pi-search-plus', routerLink: ['/explorer'] },
                    // { label: 'Product Insights', icon: 'pi pi-fw pi-eye', routerLink: ['/product'] },
                    { label: 'Customer Insights', icon: 'pi pi-fw pi-user', routerLink: ['/customer-insights'] },
                ]
            }
        ];
    }
}
