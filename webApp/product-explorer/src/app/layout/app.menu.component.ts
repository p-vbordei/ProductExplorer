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
        if (!this.layoutService.state.selectedInvestigationId) {
            this.model = [
                {
                    label: 'Investigation',
                    items: [
                        { label: 'Home', icon: 'pi pi-fw pi-home', routerLink: ['/'] },
                    ]
                }
            ];
        } else if (this.layoutService.state.selectedInvestigationId) {
            this.model = [
                {
                    label: 'Investigations',
                    items: [
                        { label: 'Home', icon: 'pi pi-fw pi-home', routerLink: ['/'] },
                    ]
                },
                {
                    label: 'Investigation Details',
                    items: [
                        { label: 'Customer Insights', icon: 'pi pi-fw pi-user', routerLink: ['/investigation-details', this.layoutService.state.selectedInvestigationId, 'customer-insights']},
                    ]
                }
            ];
        }
    }
}
