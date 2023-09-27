import { Injectable, inject } from '@angular/core';
import { Firestore, collection, collectionData, getDocs, onSnapshot  } from '@angular/fire/firestore';
import { Observable, from, throwError} from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class InvestigationsService {
  firestore: Firestore = inject(Firestore)
  investigations$: Observable<any[]>;
  private readonly url: string = environment.beUrl;

  constructor(private authService: AuthService, private http: HttpClient) { }

  getInvestigationCollections(): Observable<any[]> {
    const userId = this.authService.userId;
    const investigationCollectionsRef = collection(this.firestore, 'investigations', userId, 'investigationCollections');
    
    // Return an Observable that listens for real-time changes
    return new Observable(observer => {
      const unsubscribe = onSnapshot(investigationCollectionsRef, snapshot => {
        const investigations = [];
        snapshot.forEach(doc => {
          investigations.push({ id: doc.id, ...doc.data() });
        });
        observer.next(investigations);
      }, 
      error => observer.error(error));
  
      // Return the unsubscribe function, which will be called when the consumer of this observable unsubscribes.
      return unsubscribe;
    });
  }

  postRunEndToEndInvestigation(asinString: string, name: string) {
    const userId = this.authService.userId;
    const asinArray = asinString.match(/\bB[0-9A-Z]{9}\b/g);

    if (!asinArray || asinArray.length === 0) {
      return throwError(() => new Error("No ASINs found in the provided string."));
    }
    const body = {
      asinList: asinArray,
      name: name,
      userId: userId
    };

    return this.http.post(`${this.url}/run_end_to_end_investigation`, body);
  }
}
