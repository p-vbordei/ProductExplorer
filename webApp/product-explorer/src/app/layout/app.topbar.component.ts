import { Component, ElementRef, ViewChild, OnInit } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { LayoutService } from "./service/app.layout.service";
import { AuthService } from '../demo/service/auth.service';

@Component({
    selector: 'app-topbar',
    templateUrl: './app.topbar.component.html'
})
export class AppTopBarComponent implements OnInit {

    items!: MenuItem[];
    menuItems: MenuItem[] = [];

    @ViewChild('menubutton') menuButton!: ElementRef;

    @ViewChild('topbarmenubutton') topbarMenuButton!: ElementRef;

    @ViewChild('topbarmenu') menu!: ElementRef;

    constructor(public layoutService: LayoutService, private authService: AuthService) { }

    ngOnInit() {    
        this.menuItems = [
            {
                label: 'Logout', 
                icon: 'pi pi-fw pi-power-off',
                command: () => {
                    this.logout();
                }

            }
        ];
    }

    async logout() {
        try {
          await this.authService.logout();
          console.log('Logged out');
        } catch (error) {
          console.error('Error:', error);
        }
      }
}
