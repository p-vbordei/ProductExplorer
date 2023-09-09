import { OnInit } from '@angular/core';
import { Component } from '@angular/core';
import { LayoutService } from './service/app.layout.service';
import { Subscription } from 'rxjs';

@Component({
    selector: 'app-menu',
    templateUrl: './app.menu.component.html'
})
export class AppMenuComponent implements OnInit {

    model: any[] = [];
    private stateSubscription: Subscription;

    constructor(public layoutService: LayoutService) { }

    ngOnInit() {
        if (this.layoutService.state.selectedInvestigationId) {
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
        } else {
            this.model = [
                {
                    label: 'Investigation',
                    items: [
                        { label: 'Home', icon: 'pi pi-fw pi-home', routerLink: ['/'] },
                    ]
                }
            ];
        }
        
        this.stateSubscription = this.layoutService.stateUpdate$.subscribe(state => {
            if (state.selectedInvestigationId) {
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
        });
    } 

    ngOnDestroy() {
        if (this.stateSubscription) {
            this.stateSubscription.unsubscribe();
        }
    }
}
